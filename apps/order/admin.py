from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, OrderRefund
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import path
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404
from apps.member.models import Member

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_price', 'created_at', 'updated_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'user__username')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('价格信息', {
            'fields': ('total_amount', 'shipping_fee', 'discount_amount')
        }),
        ('支付信息', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('收货信息', {
            'fields': ('shipping_address',)
        }),
        ('其他信息', {
            'fields': ('remark', 'created_at', 'updated_at')
        }),
    )
    
    # 添加自定义按钮
    change_form_template = 'admin/order/order/change_form.html'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/update_status/',
                self.admin_site.admin_view(self.update_status_view),
                name='order_update_status',
            ),
        ]
        return custom_urls + urls
    
    def update_status_view(self, request, object_id):
        """处理状态更新请求"""
        order = get_object_or_404(Order, pk=object_id)
        
        # 如果是POST请求，处理状态更新
        if request.method == 'POST':
            new_status = request.POST.get('new_status')
            
            # 验证状态是否有效
            valid_statuses = [status[0] for status in Order.STATUS_CHOICES]
            if new_status in valid_statuses:
                old_status = order.status
                
                # 更新订单状态
                order.status = new_status
                order.save()
                
                # 创建状态变更记录
                OrderStatusHistory.objects.create(
                    order=order,
                    from_status=old_status,
                    to_status=new_status,
                    remark=f'管理员更新订单状态: {dict(Order.STATUS_CHOICES).get(old_status)} → {dict(Order.STATUS_CHOICES).get(new_status)}',
                    operator=request.user
                )
                
                # 特殊状态处理
                if new_status == 'paid' and not hasattr(order, 'paid_at'):
                    # 如果订单状态变为已支付，尝试更新支付时间
                    try:
                        order.paid_at = timezone.now()
                        order.save(update_fields=['paid_at'])
                    except:
                        # 如果paid_at字段不存在，忽略错误
                        pass
                
                self.message_user(request, f'订单 {order.order_number} 状态已更新为 {dict(Order.STATUS_CHOICES).get(new_status)}')
            else:
                self.message_user(request, f'无效的订单状态: {new_status}', level=messages.ERROR)
            
            # 重定向回订单详情页
            return HttpResponseRedirect(f"../")
        
        # 如果是GET请求，显示状态选择表单
        context = {
            'title': f'更新订单 {order.order_number} 的状态',
            'order': order,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
            'original': order,
            'has_change_permission': self.has_change_permission(request, order),
            'status_choices': [
                ('shipped', '已发货'),
                ('delivered', '已送达'),
                ('completed', '已完成'),
                ('refunding', '退款中'),
                ('refunded', '已退款'),
                ('cancelled', '已取消')
            ],
            'current_status': order.status,
            'current_status_display': dict(Order.STATUS_CHOICES).get(order.status)
        }
        
        return TemplateResponse(
            request,
            'admin/order/order/update_status.html',
            context,
        )
    
    def save_model(self, request, obj, form, change):
        """重写保存方法，记录订单状态变更历史"""
        if change and 'status' in form.changed_data:
            old_obj = Order.objects.get(pk=obj.pk)
            # 如果状态发生变化
            if old_obj.status != obj.status:
                # 保存对象
                super().save_model(request, obj, form, change)
                
                # 创建状态变更历史记录
                OrderStatusHistory.objects.create(
                    order=obj,
                    from_status=old_obj.status,
                    to_status=obj.status,
                    remark=f'管理员修改订单状态: {old_obj.get_status_display()} → {obj.get_status_display()}',
                    operator=request.user
                )
                return
        
        # 其他情况正常保存
        super().save_model(request, obj, form, change)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_name', 'quantity', 'price', 'subtotal')
    search_fields = ('product_name',)
    list_filter = ('order__status',)

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'from_status', 'to_status', 'operator', 'created_at')
    list_filter = ('from_status', 'to_status', 'created_at')
    search_fields = ('order__order_number',)
    readonly_fields = ('created_at',)
    actions = ['delete_and_revert_status']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/delete_and_revert/',
                self.admin_site.admin_view(self.delete_and_revert_view),
                name='order_statushistory_delete_revert',
            ),
        ]
        return custom_urls + urls
    
    def delete_and_revert_view(self, request, object_id):
        """处理删除状态历史并恢复订单状态的请求"""
        status_history = get_object_or_404(OrderStatusHistory, pk=object_id)
        order = status_history.order
        
        # 如果是POST请求，处理删除和恢复
        if request.method == 'POST':
            if request.POST.get('confirm') == 'yes':
                # 获取前一个状态
                previous_status = status_history.from_status
                current_status = status_history.to_status
                
                # 检查这是否是最新的状态变更
                latest_history = OrderStatusHistory.objects.filter(
                    order=order
                ).order_by('-created_at').first()
                
                if latest_history and latest_history.id == status_history.id:
                    # 这是最新的状态变更，可以安全地恢复订单状态
                    order.status = previous_status
                    order.save()
                    
                    # 创建新的状态历史记录
                    OrderStatusHistory.objects.create(
                        order=order,
                        from_status=current_status,
                        to_status=previous_status,
                        remark=f'管理员撤销状态变更，恢复为: {dict(Order.STATUS_CHOICES).get(previous_status)}',
                        operator=request.user
                    )
                    
                    # 删除原状态历史记录
                    status_history.delete()
                    
                    self.message_user(
                        request, 
                        f'已删除状态历史记录并将订单 {order.order_number} 的状态恢复为 {dict(Order.STATUS_CHOICES).get(previous_status)}',
                        messages.SUCCESS
                    )
                else:
                    # 这不是最新的状态变更，只删除记录但不修改订单状态
                    status_history.delete()
                    self.message_user(
                        request, 
                        f'已删除状态历史记录，但由于这不是最新的状态变更，订单状态保持不变',
                        messages.WARNING
                    )
            
            # 重定向回订单历史列表页
            return HttpResponseRedirect(f"/admin/order/orderstatushistory/")
        
        # 如果是GET请求，显示确认页面
        context = {
            'title': '删除状态历史并恢复订单状态',
            'status_history': status_history,
            'order': order,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
            'from_status_display': dict(Order.STATUS_CHOICES).get(status_history.from_status),
            'to_status_display': dict(Order.STATUS_CHOICES).get(status_history.to_status),
            'latest_history': OrderStatusHistory.objects.filter(order=order).order_by('-created_at').first(),
        }
        
        return TemplateResponse(
            request,
            'admin/order/orderstatushistory/delete_and_revert.html',
            context,
        )
    
    def delete_and_revert_status(self, request, queryset):
        """批量删除状态历史并恢复订单状态"""
        # 只处理每个订单的最新状态记录
        processed_orders = set()
        success_count = 0
        skipped_count = 0
        
        for status_history in queryset.order_by('-created_at'):
            order = status_history.order
            
            # 如果已经处理过这个订单，跳过
            if order.id in processed_orders:
                skipped_count += 1
                continue
                
            # 检查这是否是最新的状态变更
            latest_history = OrderStatusHistory.objects.filter(
                order=order
            ).order_by('-created_at').first()
            
            if latest_history and latest_history.id == status_history.id:
                # 这是最新的状态变更，可以安全地恢复订单状态
                previous_status = status_history.from_status
                current_status = status_history.to_status
                
                order.status = previous_status
                order.save()
                
                # 创建新的状态历史记录
                OrderStatusHistory.objects.create(
                    order=order,
                    from_status=current_status,
                    to_status=previous_status,
                    remark=f'管理员批量撤销状态变更，恢复为: {dict(Order.STATUS_CHOICES).get(previous_status)}',
                    operator=request.user
                )
                
                # 删除原状态历史记录
                status_history.delete()
                
                processed_orders.add(order.id)
                success_count += 1
            else:
                # 这不是最新的状态变更，只删除记录但不修改订单状态
                status_history.delete()
                skipped_count += 1
        
        if success_count > 0:
            self.message_user(
                request, 
                f'已成功恢复 {success_count} 个订单的状态，跳过 {skipped_count} 条记录',
                messages.SUCCESS
            )
        else:
            self.message_user(
                request, 
                f'已删除 {skipped_count} 条状态历史记录，但没有恢复任何订单状态（只有最新的状态记录才会导致订单状态恢复）',
                messages.WARNING
            )
    
    delete_and_revert_status.short_description = "删除所选记录并恢复订单状态（如果可能）"

@admin.register(OrderRefund)
class OrderRefundAdmin(admin.ModelAdmin):
    list_display = ('refund_number', 'order', 'type', 'status', 'refund_amount', 'created_at')
    list_filter = ('type', 'status', 'created_at')
    search_fields = ('refund_number', 'order__order_number')
    readonly_fields = ('refund_number', 'created_at')
    actions = ['approve_and_complete_refund']
    
    def save_model(self, request, obj, form, change):
        """重写保存方法，当状态变为已同意时自动完成退款流程"""
        if change and 'status' in form.changed_data:
            old_obj = OrderRefund.objects.get(pk=obj.pk)
            # 如果状态从其他状态变为已同意
            if old_obj.status != 'approved' and obj.status == 'approved':
                # 保存对象
                super().save_model(request, obj, form, change)
                # 自动完成退款流程
                self._complete_refund(request, obj)
                return
        
        # 其他情况正常保存
        super().save_model(request, obj, form, change)
    
    def approve_and_complete_refund(self, request, queryset):
        """批量同意并完成退款"""
        for refund in queryset:
            if refund.status == 'pending':
                # 更新为已同意状态
                refund.status = 'approved'
                refund.processed_at = timezone.now()
                refund.save()
                
                # 完成退款流程
                self._complete_refund(request, refund)
        
        self.message_user(request, f"已处理 {queryset.count()} 条退款申请", messages.SUCCESS)
    
    approve_and_complete_refund.short_description = "同意并完成选中的退款申请"
    
    def _complete_refund(self, request, refund):
        """完成退款流程"""
        try:
            # 更新退款状态为已完成
            refund.status = 'completed'
            refund.processed_at = timezone.now()
            refund.save()
            
            # 更新订单状态为已退款
            refund.order.status = 'refunded'
            refund.order.save()
            
            # 如果原订单使用钱包支付，退款金额返回钱包
            if refund.order.payment_method == 'balance':
                try:
                    member = Member.objects.get(user=refund.order.user)
                    from decimal import Decimal
                    old_wallet_balance = member.balance
                    refund_amount_decimal = Decimal(str(refund.refund_amount))
                    member.balance += refund_amount_decimal
                    member.save()
                    print(f"钱包退款完成：用户 {refund.order.user.username}，订单 {refund.order.order_number}，退款金额 ¥{refund.refund_amount}，余额 {old_wallet_balance} -> {member.balance}")
                    self.message_user(request, f"退款金额 ¥{refund.refund_amount} 已退回用户钱包", messages.INFO)
                except Member.DoesNotExist:
                    self.message_user(request, f"用户会员信息不存在，无法退款到钱包", messages.WARNING)
                except Exception as e:
                    self.message_user(request, f"钱包退款失败: {str(e)}", messages.ERROR)
            
            # 记录订单状态变更
            OrderStatusHistory.objects.create(
                order=refund.order,
                from_status='refunding',
                to_status='refunded',
                remark='管理员完成退款',
                operator=request.user
            )
            
            # 如果是退货退款或仅退款，返还用户使用过的优惠券
            if refund.type in ['return_refund', 'refund_only']:
                self._restore_coupon(refund.order)
            
            # 处理会员积分扣除
            self._handle_refund_points(request, refund.order)
            
            self.message_user(request, f"退款 {refund.refund_number} 已完成处理", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"处理退款 {refund.refund_number} 时出错: {str(e)}", messages.ERROR)
    
    def _handle_refund_points(self, request, order):
        """处理退款时的积分扣除"""
        try:
            from apps.member.models import Member
            from apps.member.services import PointsService
            
            # 获取会员信息
            member = Member.objects.get(user=order.user)
            
            # 使用积分服务扣除积分
            points_deducted, level_changed, old_level, new_level = PointsService.deduct_points_for_refund(
                member=member,
                order_id=order.id,
                amount=order.total_price
            )
            
            if points_deducted > 0:
                message = f"已扣除用户 {order.user.username} 的 {points_deducted} 积分"
                if level_changed:
                    message += f"，等级从 {old_level} 降至 {new_level}"
                self.message_user(request, message, messages.INFO)
                print(f"退款处理：订单 {order.order_number}，扣除 {points_deducted} 积分")
            else:
                print(f"退款处理：订单 {order.order_number}，无需扣除积分（未找到原积分记录）")
                
        except Member.DoesNotExist:
            print(f"用户 {order.user.username} 没有会员资料，跳过积分处理")
        except Exception as e:
            self.message_user(request, f"处理积分扣除时出错: {str(e)}", messages.WARNING)
            print(f"退款积分处理出错: {str(e)}")
    
    def _restore_coupon(self, order):
        """返还订单使用的优惠券"""
        from apps.member.models import MemberCoupon
        from apps.coupon.models import CouponUsageRecord
        from django.utils import timezone
        
        try:
            # 获取退款记录
            refund = OrderRefund.objects.filter(order=order, status='completed').first()
            if not refund:
                return
                
            # 查找与订单关联的会员优惠券
            member_coupons = MemberCoupon.objects.filter(order_id=order.id, status='used')
            
            if not member_coupons.exists():
                return
            
            now = timezone.now()
            for member_coupon in member_coupons:
                # 检查优惠券是否已过期
                if member_coupon.coupon.end_date < now:
                    continue
                
                # 返还优惠券
                member_coupon.status = 'available'  # 确保状态设置为available
                member_coupon.used_at = None
                member_coupon.order_id = None
                member_coupon.save()
                
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
                        record.admin_remark = '管理员退还优惠券（退款完成）'
                        record.save()
            
        except Exception as e:
            print(f"返还优惠券失败: {str(e)}")