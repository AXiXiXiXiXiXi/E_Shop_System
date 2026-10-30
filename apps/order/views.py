from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from .models import Order, OrderItem, OrderStatusHistory, OrderRefund
from .serializers import (
    OrderSerializer, OrderItemSerializer, OrderStatusHistorySerializer,
    OrderRefundSerializer, OrderCreateSerializer
)
# 导入会员积分服务
from apps.member.models import Member
from apps.member.services import PointsService

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.all()  # 添加queryset属性以支持路由注册
    
    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)
        status_filter = self.request.query_params.get('status')
        order_number = self.request.query_params.get('order_number')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if order_number:
            queryset = queryset.filter(order_number=order_number)
            
        return queryset.order_by('-created_at')
        
    def retrieve(self, request, pk=None):
        """获取单个订单详情，支持通过ID或订单号查找"""
        try:
            # 检查pk是否为订单号格式
            if pk and pk.startswith('ORD'):
                try:
                    # 使用订单号查找
                    order = Order.objects.get(order_number=pk, user=request.user)
                    serializer = self.get_serializer(order)
                    return Response(serializer.data)
                except Order.DoesNotExist:
                    pass  # 继续尝试用ID查找
                
            # 默认通过ID查找
            order = self.get_object()
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': f'未找到订单: {str(e)}'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消订单"""
        order = self.get_object()
        if not order.can_cancel:
            return Response(
                {'error': '订单当前状态不允许取消'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cancel_reason = request.data.get('reason', '')
        order.status = 'cancelled'
        order.cancel_reason = cancel_reason
        order.save()
        
        # 记录状态变更
        OrderStatusHistory.objects.create(
            order=order,
            from_status='pending',
            to_status='cancelled',
            remark=f'用户取消订单: {cancel_reason}',
            operator=request.user
        )
        
        # 如果订单关联了优惠券但还未使用，释放优惠券关联
        if order.meta and 'coupon_id' in order.meta:
            print(f"取消订单，检查是否需要释放优惠券 {order.meta.get('coupon_id')}")
            # 仅在优惠券尚未被使用时执行（在支付前取消订单）
            if not order.meta.get('coupon_used', False):
                # 清除订单与优惠券的关联
                order.meta['coupon_released'] = True
                order.save(update_fields=['meta'])
                print(f"已释放订单 {order.order_number} 关联的优惠券 {order.meta.get('coupon_id')}")
        
        return Response({'message': '订单已取消'})
    
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """支付订单"""
        order = self.get_object()
        if not order.can_pay:
            return Response(
                {'error': '订单当前状态不允许支付'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_method = request.data.get('payment_method')
        if not payment_method:
            return Response(
                {'error': '请选择支付方式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 确保timezone和Member始终可用
        from django.utils import timezone
        from apps.member.models import Member
        from django.db import transaction
        
        try:
            with transaction.atomic():
                # 如果是钱包支付，需要检查余额并扣除
                if payment_method == 'balance':
                    try:
                        member = Member.objects.get(user=order.user)
                    except Member.DoesNotExist:
                        return Response(
                            {'error': '会员信息不存在，无法使用钱包支付'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # 检查钱包余额是否足够
                    order_total = order.total_price
                    if member.balance < order_total:
                        return Response(
                            {'error': f'钱包余额不足。当前余额：¥{member.balance}，订单金额：¥{order_total}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # 扣除钱包余额
                    old_balance = member.balance
                    member.balance -= order_total
                    member.save()
                    
                    print(f"钱包支付成功：用户 {order.user.username}，订单 {order.order_number}，扣除金额 ¥{order_total}，余额 {old_balance} -> {member.balance}")
                
                elif payment_method in ['alipay', 'wechat']:
                    # 支付宝和微信支付的处理逻辑
                    print(f"{payment_method.upper()}支付：用户 {order.user.username}，订单 {order.order_number}，金额 ¥{order.total_price}")
                
                # 通用的订单状态更新逻辑（所有支付方式都执行）
                order.status = 'paid'
                order.payment_method = payment_method
                order.paid_at = timezone.now()
                order.payment_transaction_id = f'PAY{timezone.now().strftime("%Y%m%d%H%M%S")}{order.id}'
                order.save()
                
                # 记录状态变更
                OrderStatusHistory.objects.create(
                    order=order,
                    from_status='pending',
                    to_status='paid',
                    remark=f'订单支付成功，支付方式: {order.get_payment_method_display()}',
                    operator=request.user
                )
        
        except Exception as e:
            print(f"支付处理失败: {str(e)}")
            return Response(
                {'error': f'支付处理失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        # 处理优惠券：如果订单关联了优惠券，现在才标记为已使用
        if order.meta and 'coupon_id' in order.meta and not order.meta.get('coupon_used', False):
            coupon_id = order.meta['coupon_id']
            try:
                from apps.member.models import MemberCoupon
                # 不在这里导入Member，因为已经在方法开始时导入
                from apps.coupon.models import CouponUsageRecord, Coupon
                
                # 获取会员优惠券
                member = Member.objects.get(user=order.user)
                member_coupon = MemberCoupon.objects.get(id=coupon_id, member=member)
                
                # 更新优惠券状态
                member_coupon.status = 'used'
                member_coupon.used_at = timezone.now()
                member_coupon.order_id = order.id
                member_coupon.save()
                
                # 创建优惠券使用记录
                try:
                    coupon_obj = Coupon.objects.get(code=member_coupon.coupon.code)
                except Coupon.DoesNotExist:
                    # 如果不存在，创建一个
                    coupon_type = 'full_reduction' if member_coupon.coupon.type == 'fixed' else (
                        'discount' if member_coupon.coupon.type == 'discount' else 'free_shipping'
                    )
                    coupon_obj = Coupon.objects.create(
                        code=member_coupon.coupon.code,
                        coupon_type=coupon_type,
                        discount_amount=member_coupon.coupon.value if coupon_type != 'discount' else None,
                        discount_rate=member_coupon.coupon.value if coupon_type == 'discount' else None,
                        min_purchase_amount=member_coupon.coupon.min_amount,
                        start_time=member_coupon.coupon.start_date,
                        end_time=member_coupon.coupon.end_date,
                        is_platform=True
                    )
                
                # 创建使用记录
                CouponUsageRecord.objects.create(
                    member_id=member.id,
                    coupon=coupon_obj,
                    order_id=order.id,
                    coupon_code=member_coupon.coupon.code,
                    coupon_type=coupon_obj.coupon_type,
                    discount_amount=order.discount_amount
                )
                
                # 更新订单meta数据，标记优惠券已使用
                order.meta['coupon_used'] = True
                order.save(update_fields=['meta'])
                
                print(f"支付成功后，优惠券 {coupon_id} 已标记为已使用")
            except Exception as e:
                print(f"支付成功后处理优惠券失败: {str(e)}")
        
        # 更新会员订单统计数据
        try:
            member = Member.objects.get(user=order.user)
            member.total_orders = member.total_orders + 1
            member.total_spent = member.total_spent + order.total_amount
            member.save(update_fields=['total_orders', 'total_spent', 'updated_at'])
        except Member.DoesNotExist:
            # 用户没有会员信息，忽略更新
            pass
        
        # 返回更详细的支付结果信息
        return Response({
            'message': '支付成功',
            'transaction_id': order.payment_transaction_id,
            'payment_method': order.payment_method,
            'payment_method_display': order.get_payment_method_display(),
            'paid_at': order.paid_at,
            'order_status': order.status,
            'order_status_display': order.get_status_display(),
            'order_id': order.id,
            'order_number': order.order_number,
        })
    
    @action(detail=True, methods=['post'])
    def confirm_receipt(self, request, pk=None):
        """确认收货"""
        order = self.get_object()
        if not order.can_confirm_receipt:
            return Response(
                {'error': '订单当前状态不允许确认收货'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'completed'
        order.save()
        
        # 记录状态变更
        OrderStatusHistory.objects.create(
            order=order,
            from_status='delivered',
            to_status='completed',
            remark='用户确认收货',
            operator=request.user
        )
        
        # 处理会员积分
        try:
            from apps.member.models import Member
            from apps.member.services import PointsService
            
            member = Member.objects.get(user=order.user)
            
            # 使用积分服务添加积分（1元=1积分）
            points_added, level_changed, old_level, new_level = PointsService.add_points_for_order(
                member=member,
                order_id=order.id,
                amount=order.total_price
            )
            
            response_data = {
                'message': '确认收货成功',
                'points_added': points_added,
                'current_points': member.points
            }
            
            if level_changed:
                response_data['level_upgraded'] = True
                response_data['old_level'] = old_level
                response_data['new_level'] = new_level
                response_data['level_message'] = f'恭喜！您的会员等级已从 {old_level} 升级到 {new_level}！'
            
            print(f"订单 {order.order_number} 完成，用户 {order.user.username} 获得 {points_added} 积分")
            
            return Response(response_data)
            
        except Member.DoesNotExist:
            print(f"用户 {order.user.username} 没有会员资料，跳过积分处理")
            return Response({'message': '确认收货成功'})
        except Exception as e:
            print(f"处理积分时出错: {str(e)}")
            # 即使积分处理失败，确认收货也应该成功
            return Response({'message': '确认收货成功，积分处理异常'})
    
    @action(detail=False, methods=['post'], url_path='by-number/(?P<order_number>[^/.]+)/confirm_receipt')
    def confirm_receipt_by_order_number(self, request, order_number=None):
        """通过订单号确认收货"""
        try:
            print(f"通过订单号确认收货: {order_number}")
            # 使用订单号查找
            order = Order.objects.get(order_number=order_number, user=request.user)
            
            if not order.can_confirm_receipt:
                print(f"订单不可确认收货: {order.order_number}, 状态: {order.status}")
                return Response(
                    {'error': '订单当前状态不允许确认收货'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            order.status = 'completed'
            order.save()
            
            # 记录状态变更
            OrderStatusHistory.objects.create(
                order=order,
                from_status='delivered',
                to_status='completed',
                remark='用户确认收货',
                operator=request.user
            )
            
            # 处理会员积分
            try:
                from apps.member.models import Member
                from apps.member.services import PointsService
                
                member = Member.objects.get(user=order.user)
                
                # 使用积分服务添加积分（1元=1积分）
                points_added, level_changed, old_level, new_level = PointsService.add_points_for_order(
                    member=member,
                    order_id=order.id,
                    amount=order.total_price
                )
                
                response_data = {
                    'message': '确认收货成功',
                    'points_added': points_added,
                    'current_points': member.points
                }
                
                if level_changed:
                    response_data['level_upgraded'] = True
                    response_data['old_level'] = old_level
                    response_data['new_level'] = new_level
                    response_data['level_message'] = f'恭喜！您的会员等级已从 {old_level} 升级到 {new_level}！'
                
                print(f"订单 {order.order_number} 完成，用户 {order.user.username} 获得 {points_added} 积分")
                
                return Response(response_data)
                
            except Member.DoesNotExist:
                print(f"用户 {order.user.username} 没有会员资料，跳过积分处理")
                return Response({'message': '确认收货成功'})
            except Exception as e:
                print(f"处理积分时出错: {str(e)}")
                # 即使积分处理失败，确认收货也应该成功
                return Response({'message': '确认收货成功，积分处理异常'})
            
        except Order.DoesNotExist:
            return Response(
                {'detail': f'未找到订单号为 {order_number} 的订单'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"确认收货出错: {str(e)}")
            return Response(
                {'detail': f'确认收货失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def tracking(self, request, pk=None):
        """查询物流信息"""
        order = self.get_object()
        if not order.tracking_number:
            return Response(
                {'error': '订单暂无物流信息'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 模拟物流信息
        tracking_info = {
            'tracking_number': order.tracking_number,
            'shipping_company': order.shipping_company,
            'status': order.status,
            'shipped_at': order.shipped_at,
            'delivered_at': order.delivered_at,
            'tracking_details': [
                {
                    'time': order.shipped_at,
                    'status': '已发货',
                    'description': f'您的订单已从仓库发出，物流公司: {order.shipping_company}'
                },
                {
                    'time': order.delivered_at or timezone.now(),
                    'status': '运输中' if not order.delivered_at else '已送达',
                    'description': '商品正在运输途中' if not order.delivered_at else '商品已送达收货地址'
                }
            ]
        }
        
        return Response(tracking_info)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """订单统计"""
        user_orders = Order.objects.filter(user=request.user)
        
        stats = {
            'total_orders': user_orders.count(),
            'pending_orders': user_orders.filter(status='pending').count(),
            'paid_orders': user_orders.filter(status='paid').count(),
            'shipped_orders': user_orders.filter(status='shipped').count(),
            'completed_orders': user_orders.filter(status='completed').count(),
            'cancelled_orders': user_orders.filter(status='cancelled').count(),
            'total_amount': sum(order.total_price for order in user_orders.filter(status__in=['paid', 'shipped', 'delivered', 'completed'])),
        }
        
        return Response(stats)

    @action(detail=False, methods=['get'], url_path='by-number/(?P<order_number>[^/.]+)')
    def retrieve_by_order_number(self, request, order_number=None):
        """通过订单号获取订单详情"""
        try:
            print(f"通过订单号获取订单: {order_number}")
            # 使用订单号查找
            order = Order.objects.get(order_number=order_number, user=request.user)
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response(
                {'detail': f'未找到订单号为 {order_number} 的订单'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"获取订单出错: {str(e)}")
            return Response(
                {'detail': f'获取订单失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='by-number/(?P<order_number>[^/.]+)/cancel')
    def cancel_by_order_number(self, request, order_number=None):
        """通过订单号取消订单"""
        try:
            print(f"通过订单号取消订单: {order_number}")
            # 使用订单号查找
            order = Order.objects.get(order_number=order_number, user=request.user)
            
            if not order.can_cancel:
                print(f"订单不可取消: {order.order_number}, 状态: {order.status}")
                return Response(
                    {'error': '订单当前状态不允许取消'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cancel_reason = request.data.get('reason', '')
            order.status = 'cancelled'
            order.cancel_reason = cancel_reason
            order.save()
            
            # 记录状态变更
            OrderStatusHistory.objects.create(
                order=order,
                from_status='pending',
                to_status='cancelled',
                remark=f'用户取消订单: {cancel_reason}',
                operator=request.user
            )
            
            # 如果订单关联了优惠券但还未使用，释放优惠券关联
            if order.meta and 'coupon_id' in order.meta:
                print(f"取消订单，检查是否需要释放优惠券 {order.meta.get('coupon_id')}")
                # 仅在优惠券尚未被使用时执行（在支付前取消订单）
                if not order.meta.get('coupon_used', False):
                    # 清除订单与优惠券的关联
                    order.meta['coupon_released'] = True
                    order.save(update_fields=['meta'])
                    print(f"已释放订单 {order.order_number} 关联的优惠券 {order.meta.get('coupon_id')}")
            
            return Response({'message': '订单已取消'})
            
        except Order.DoesNotExist:
            return Response(
                {'detail': f'未找到订单号为 {order_number} 的订单'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"取消订单出错: {str(e)}")
            return Response(
                {'detail': f'取消订单失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def complete_order(self, request, pk=None):
        """管理员完成订单"""
        order = self.get_object()
        
        # 检查订单状态
        if order.status not in ['paid', 'processing', 'shipped']:
            return Response(
                {'error': '只有已支付、处理中或已发货的订单可以标记为已完成'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 记录原始状态
        previous_status = order.status
        
        # 更新订单状态
        order.status = 'completed'
        order.save()
        
        # 创建状态变更记录
        OrderStatusHistory.objects.create(
            order=order,
            from_status=previous_status,
            to_status='completed',
            remark='管理员手动完成订单',
            operator=request.user
        )
        
        # 处理会员积分
        try:
            from apps.member.models import Member
            from apps.member.services import PointsService
            
            member = Member.objects.get(user=order.user)
            
            # 使用积分服务添加积分（1元=1积分）
            points_added, level_changed, old_level, new_level = PointsService.add_points_for_order(
                    member=member,
                order_id=order.id,
                amount=order.total_price
            )
            
            response_data = {
                'message': '订单已标记为已完成',
                'order_number': order.order_number,
                'status': order.status,
                'status_display': order.get_status_display(),
                'points_added': points_added,
                'current_points': member.points
            }
            
            if level_changed:
                response_data['level_upgraded'] = True
                response_data['old_level'] = old_level
                response_data['new_level'] = new_level
                response_data['level_message'] = f'用户会员等级已从 {old_level} 升级到 {new_level}！'
            
            print(f"管理员完成订单 {order.order_number}，用户 {order.user.username} 获得 {points_added} 积分")
            
            return Response(response_data)
            
        except Member.DoesNotExist:
            # 用户没有会员信息，仅返回订单信息
            return Response({
                'message': '订单已标记为已完成',
                'order_number': order.order_number,
                'status': order.status,
                'status_display': order.get_status_display()
            })
        except Exception as e:
            # 积分处理出错，返回警告信息
            return Response({
                'message': '订单已标记为已完成，但积分处理失败',
                'order_number': order.order_number,
                'status': order.status,
                'error': str(e)
            }, status=status.HTTP_207_MULTI_STATUS)

class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    queryset = OrderItem.objects.all()  # 添加queryset属性以支持路由注册
    
    def get_queryset(self):
        return OrderItem.objects.filter(order__user=self.request.user)

class OrderStatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderStatusHistorySerializer
    permission_classes = [IsAuthenticated]
    queryset = OrderStatusHistory.objects.all()  # 添加queryset属性以支持路由注册
    
    def get_queryset(self):
        return OrderStatusHistory.objects.filter(order__user=self.request.user)

class OrderRefundViewSet(viewsets.ModelViewSet):
    serializer_class = OrderRefundSerializer
    permission_classes = [IsAuthenticated]
    queryset = OrderRefund.objects.all()  # 添加queryset属性以支持路由注册
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return OrderRefund.objects.all()
        return OrderRefund.objects.filter(order__user=self.request.user)
    
    def perform_create(self, serializer):
        # 设置关联的用户
        serializer.save()
        
        # 如果是用户提交的退款申请，更新订单状态
        if not self.request.user.is_staff and serializer.instance.order.status not in ['refunding', 'refunded']:
            serializer.instance.order.status = 'refunding'
            serializer.instance.order.save()
    
    @action(detail=False, methods=['post'])
    def apply_refund(self, request):
        """用户申请退款"""
        # 从请求数据中直接获取order_id
        order_id = request.data.get('order_id')
        if not order_id:
            return Response(
                {'error': '订单ID是必需的'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取订单信息
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {'error': '未找到相关订单或您无权操作此订单'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查订单是否可以申请退款
        if order.status not in ['paid', 'processing', 'shipped', 'delivered', 'completed']:
            return Response(
                {'error': f'订单状态为 {order.get_status_display()} 不可申请退款'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查是否已存在处理中的退款申请
        if OrderRefund.objects.filter(order=order, status__in=['pending', 'approved', 'processing']).exists():
            return Response(
                {'error': '此订单已有处理中的退款申请，请勿重复提交'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 准备序列化器数据
        refund_data = request.data.copy()
        refund_data['order'] = order.id  # 确保使用正确的order字段
        
        # 验证请求数据
        serializer = self.get_serializer(data=refund_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 保存退款申请
        refund = serializer.save()
        
        # 更新订单状态为退款中
        order.status = 'refunding'
        order.save()
        
        # 记录订单状态变更
        OrderStatusHistory.objects.create(
            order=order,
            from_status=order.status,
            to_status='refunding',
            remark=f'用户申请退款: {refund.reason}',
            operator=request.user
        )
        
        return Response({
            'message': '退款申请已提交',
            'refund_id': refund.id,
            'refund_number': refund.refund_number,
            'status': refund.status
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """管理员审核通过退款申请"""
        if not request.user.is_staff:
            return Response({'error': '您没有权限执行此操作'}, status=status.HTTP_403_FORBIDDEN)
        
        refund = self.get_object()
        
        # 检查退款请求状态
        if refund.status != 'pending':
            return Response(
                {'error': '只能审核待处理的退款申请'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新退款请求状态
        refund.status = 'approved'
        refund.admin_remark = request.data.get('admin_remark', '')
        refund.save()
        
        # 更新订单状态继续保持为退款中
        refund.order.status = 'refunding'
        refund.order.save()
        
        # 记录订单状态变更
        OrderStatusHistory.objects.create(
            order=refund.order,
            from_status=refund.order.status,
            to_status='refunding',
            remark=f'管理员审核通过退款申请，备注：{refund.admin_remark}',
            operator=request.user
        )
        
        return Response({'message': '退款申请已审核通过'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """管理员拒绝退款申请"""
        if not request.user.is_staff:
            return Response({'error': '您没有权限执行此操作'}, status=status.HTTP_403_FORBIDDEN)
        
        refund = self.get_object()
        
        # 检查退款请求状态
        if refund.status != 'pending':
            return Response(
                {'error': '只能拒绝待处理的退款申请'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新退款请求状态
        refund.status = 'rejected'
        refund.admin_remark = request.data.get('admin_remark', '')
        refund.save()
        
        # 恢复订单状态
        previous_status = request.data.get('previous_status', 'paid')
        refund.order.status = previous_status
        refund.order.save()
        
        # 记录订单状态变更
        OrderStatusHistory.objects.create(
            order=refund.order,
            from_status='refunding',
            to_status=previous_status,
            remark=f'管理员拒绝退款申请，备注：{refund.admin_remark}',
            operator=request.user
        )
        
        return Response({'message': '退款申请已拒绝'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def complete_refund(self, request, pk=None):
        """管理员完成退款并处理积分扣除"""
        refund = self.get_object()
        
        # 检查退款请求状态
        if refund.status != 'approved':
            return Response(
                {'error': '退款请求未被批准，无法完成退款'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # 更新退款状态为已完成
            refund.status = 'completed'
            refund.processed_at = timezone.now()
            refund.save()
            
            try:
                # 获取关联订单
                order = Order.objects.get(id=refund.order_id)
                
                # 如果是全额退款或订单取消，更新订单状态
                if refund.type == 'full' or refund.refund_amount >= order.total_price:
                    order.status = 'refunded'
                    order.save(update_fields=['status', 'updated_at'])
                
                # 记录订单状态变更
                OrderStatusHistory.objects.create(
                    order=order,
                    from_status='completed',  # 假设订单之前是已完成状态
                    to_status='refunded',
                    remark=f'订单已退款，退款单号: {refund.refund_number}',
                    operator=request.user
                )
                
                try:
                    # 获取会员信息
                    member = Member.objects.get(user=order.user)
                    
                    # 如果原订单使用钱包支付，退款金额返回钱包
                    wallet_refunded = False
                    if order.payment_method == 'balance':
                        from decimal import Decimal
                        old_wallet_balance = member.balance
                        refund_amount_decimal = Decimal(str(refund.refund_amount))
                        member.balance += refund_amount_decimal
                        member.save()
                        wallet_refunded = True
                        print(f"钱包退款完成：用户 {order.user.username}，订单 {order.order_number}，退款金额 ¥{refund.refund_amount}，余额 {old_wallet_balance} -> {member.balance}")
                    
                    # 使用积分服务扣除积分（基于原订单）
                    points_deducted, level_changed, old_level, new_level = PointsService.deduct_points_for_refund(
                        member, order.id, order.total_price
                    )
                    
                    # 构建响应信息
                    response_data = {
                        'message': '退款已完成',
                        'refund_number': refund.refund_number,
                        'order_number': order.order_number,
                        'points_deducted': points_deducted,
                        'current_points': member.points,
                        'wallet_refunded': wallet_refunded
                    }
                    
                    # 如果钱包退款，添加钱包相关信息
                    if wallet_refunded:
                        response_data['wallet_refund_amount'] = float(refund.refund_amount)
                        response_data['current_wallet_balance'] = float(member.balance)
                        response_data['message'] = '退款已完成，退款金额已返回钱包'
                    
                    # 如果会员等级发生变化，添加到响应
                    if level_changed:
                        response_data['level_changed'] = True
                        response_data['old_level'] = old_level
                        response_data['new_level'] = new_level
                    
                    return Response(response_data)
                    
                except Member.DoesNotExist:
                    # 用户没有会员信息
                    return Response({
                        'message': '退款已完成，但用户没有会员信息，未扣除积分',
                        'refund_number': refund.refund_number,
                        'order_number': order.order_number
                    })
                except Exception as e:
                    # 积分扣除失败，但退款仍然标记为完成
                    return Response({
                        'message': f'退款已完成，但积分扣除失败: {str(e)}',
                        'refund_number': refund.refund_number,
                        'order_number': order.order_number
                    }, status=status.HTTP_207_MULTI_STATUS)
                    
            except Order.DoesNotExist:
                return Response({
                    'error': '找不到关联的订单信息'
                }, status=status.HTTP_404_NOT_FOUND)
    
    def _restore_coupon(self, order):
        """返还订单使用的优惠券"""
        from apps.member.models import MemberCoupon, Member
        from apps.coupon.models import CouponUsageRecord
        from django.utils import timezone
        
        try:
            # 获取退款记录
            refund = OrderRefund.objects.filter(order=order, status='approved').first()
            if not refund:
                print(f"订单 {order.order_number} 没有已批准的退款记录")
                return
            
            # 查找与订单关联的会员优惠券
            member_coupons = MemberCoupon.objects.filter(order_id=order.id, status='used')
            
            if not member_coupons.exists():
                print(f"订单 {order.order_number} 没有使用优惠券")
                return
            
            now = timezone.now()
            for member_coupon in member_coupons:
                # 检查优惠券是否已过期
                if member_coupon.coupon.end_date < now:
                    print(f"优惠券 {member_coupon.id} 已过期，无法返还")
                    continue
                
                # 返还优惠券
                member_coupon.status = 'available'  # 确保状态设置为available
                member_coupon.used_at = None
                member_coupon.order_id = None
                member_coupon.save()
                
                print(f"优惠券 {member_coupon.id} 已返还给用户 {member_coupon.member.user.username}")
                
                # 更新退款记录中的优惠券信息
                if refund and not refund.coupon_returned:
                    refund.coupon_returned = True
                    refund.coupon_returned_at = now
                    refund.coupon_code = member_coupon.coupon.code
                    refund.coupon_value = member_coupon.coupon.value
                    refund.coupon_type = member_coupon.coupon.type
                    refund.coupon_min_amount = member_coupon.coupon.min_amount
                    refund.save()
                    
                    # 更新优惠券使用记录状态
                    usage_records = CouponUsageRecord.objects.filter(
                        order_id=order.id,
                        coupon_code=member_coupon.coupon.code
                    )
                    for record in usage_records:
                        record.status = 'returned'
                        record.returned_at = now
                        record.admin_remark = f'系统自动退还优惠券（退款完成）'
                        record.save()
            
            print(f"订单 {order.order_number} 的优惠券已返还")
            
        except Exception as e:
            print(f"返还优惠券失败: {str(e)}")
            # 不抛出异常，避免影响主流程

class CreateOrderView(generics.CreateAPIView):
    """创建订单的API视图"""
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # 设置序列化器上下文
        serializer.context['request'] = self.request
        return serializer.save()
    
    def create(self, request, *args, **kwargs):
        try:
            print(f"接收到订单创建请求")
            print(f"请求数据: {request.data}")
            print(f"用户ID: {request.user.id}, 用户名: {request.user.username}")
            
            # 验证数据
            serializer = self.get_serializer(data=request.data)
            print(f"开始验证数据")
            
            if not serializer.is_valid():
                print(f"订单数据验证失败: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"数据验证成功，开始创建订单")
            
            # 创建订单
            try:
                order = self.perform_create(serializer)
                print(f"订单创建成功: ID={order.id}, 订单号={order.order_number}")
            
                # 返回创建的订单信息
                order_data = OrderSerializer(order).data
                
                return Response({
                    'message': '订单创建成功',
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'total_price': float(order.total_price),
                    'status': order.status,
                    'created_at': order.created_at
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                print(f"创建订单过程中出错: {str(e)}")
                import traceback
                traceback.print_exc()
                return Response({
                    'error': '订单创建过程中出错',
                    'detail': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            print(f"订单创建异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': '订单创建失败',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
