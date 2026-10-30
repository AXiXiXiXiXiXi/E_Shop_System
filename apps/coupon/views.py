from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import Coupon, CouponUsageRecord
from apps.member.models import Member, MemberCoupon
from .serializers import (
    CouponSerializer, 
    MemberCouponSerializer, CouponUsageRecordSerializer
)

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """验证优惠券是否可用"""
        code = request.data.get('code')
        total_amount = float(request.data.get('total_amount', 0))
        
        if not code:
            return Response({'error': '请提供优惠码'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            coupon = Coupon.objects.get(code=code)
            
            # 检查优惠券状态
            if coupon.status != 'active':
                return Response({'error': '优惠券已被禁用'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 检查优惠券有效期
            now = timezone.now()
            if not (coupon.start_time <= now <= coupon.end_time):
                return Response({'error': '优惠券已过期'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 检查最低消费金额
            if total_amount < float(coupon.min_purchase_amount):
                return Response({
                    'error': f'订单金额不满足使用条件，最低需要￥{coupon.min_purchase_amount}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 计算折扣金额
            discount_amount = 0
            if coupon.coupon_type == 'full_reduction':
                discount_amount = float(coupon.discount_amount)
            elif coupon.coupon_type == 'discount':
                # 打折
                discount_amount = total_amount * (1 - float(coupon.discount_rate))
            elif coupon.coupon_type == 'free_shipping':
                discount_amount = 10  # 默认运费为10元
                
            return Response({
                'valid': True,
                'coupon_id': coupon.id,
                'discount_amount': discount_amount,
                'coupon_type': coupon.coupon_type,
                'coupon_type_display': coupon.get_coupon_type_display(),
                'message': '优惠券有效'
            })
            
        except Coupon.DoesNotExist:
            return Response({'error': '无效的优惠码'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'验证优惠券失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def issue_to_member(self, request, pk=None):
        """将优惠券发放给指定会员"""
        coupon = self.get_object()
        member_id = request.data.get('member_id')
        
        if not member_id:
            return Response({'error': '缺少会员ID'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # 检查优惠券状态
            if coupon.status != 'active':
                return Response({'error': '无法发放已禁用的优惠券'}, status=status.HTTP_400_BAD_REQUEST)
                
            # 获取会员对象
            try:
                member = Member.objects.get(id=member_id)
            except Member.DoesNotExist:
                return Response({'error': '会员不存在'}, status=status.HTTP_404_NOT_FOUND)
                
            # 检查该会员是否已有此优惠券
            if MemberCoupon.objects.filter(member=member, coupon__code=coupon.code, status='available').exists():
                return Response({'error': '该会员已拥有此优惠券'}, status=status.HTTP_400_BAD_REQUEST)
                
            # 首先需要在 member.Coupon 中创建或获取对应的优惠券
            from apps.member.models import Coupon as MemberCoupon_Coupon
            member_side_coupon, created = MemberCoupon_Coupon.objects.get_or_create(
                code=coupon.code,
                defaults={
                    'name': coupon.get_coupon_type_display(),
                    'type': 'fixed' if coupon.coupon_type == 'full_reduction' else 
                           ('discount' if coupon.coupon_type == 'discount' else 'free_shipping'),
                    'value': coupon.discount_amount or coupon.discount_rate or 10,
                    'min_amount': coupon.min_purchase_amount,
                    'start_date': coupon.start_time,
                    'end_date': coupon.end_time,
                    'status': coupon.status  # 同步状态
                }
            )
            
            # 如果不是新创建的，更新状态以保持一致
            if not created:
                member_side_coupon.status = coupon.status
                member_side_coupon.save(update_fields=['status'])
            
            # 发放优惠券
            member_coupon = MemberCoupon.objects.create(
                member=member,
                coupon=member_side_coupon,
                status='available' if member_side_coupon.status == 'active' else 'inactive'
            )
            
            return Response({
                'message': '优惠券发放成功',
                'member_coupon_id': member_coupon.id
            })
            
        except Exception as e:
            return Response({'error': f'优惠券发放失败: {str(e)}'}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MemberCouponViewSet(viewsets.ModelViewSet):
    serializer_class = MemberCouponSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """获取当前会员的优惠券"""
        # 从会员服务获取当前用户的会员ID
        try:
            member = Member.objects.get(user=self.request.user)
        except:
            return MemberCoupon.objects.none()
            
        # 获取所有会员优惠券，同时考虑coupon_coupon表的status字段
        queryset = MemberCoupon.objects.filter(member=member)
        
        # 排除member_coupon表中状态为inactive的优惠券
        queryset = queryset.exclude(status='inactive')
        
        # 检查原始优惠券是否有效
        # 通过关联查询获取coupon_coupon表中状态为inactive的优惠券代码
        from django.db import connection
        inactive_coupon_codes = []
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT code FROM coupon_coupon 
                WHERE status = 'inactive'
            """)
            rows = cursor.fetchall()
            if rows:
                inactive_coupon_codes = [row[0] for row in rows]
        
        # 排除那些在coupon_coupon表中状态为inactive的优惠券
        if inactive_coupon_codes:
            queryset = queryset.exclude(coupon__code__in=inactive_coupon_codes)
        
        # 根据状态过滤参数
        status_filter = self.request.query_params.get('status')
        now = timezone.now()
        
        if status_filter:
            if status_filter == 'available':
                # 可用优惠券：未使用且未过期，或已退还的优惠券
                # 查询已退还的优惠券记录
                returned_coupon_ids = CouponUsageRecord.objects.filter(
                    member_id=member.id,
                    status='returned'
                ).values_list('coupon_id', flat=True)
                
                # 构建查询条件：状态为available且未过期，或者优惠券ID在已退还列表中
                queryset = queryset.filter(
                    (Q(status='available') & Q(coupon__end_date__gt=now)) | 
                    Q(coupon__id__in=returned_coupon_ids)
                )
            elif status_filter == 'used':
                # 已使用优惠券：状态为used且不在已退还列表中
                returned_coupon_ids = CouponUsageRecord.objects.filter(
                    member_id=member.id,
                    status='returned'
                ).values_list('coupon_id', flat=True)
                
                queryset = queryset.filter(
                    status='used'
                ).exclude(
                    coupon__id__in=returned_coupon_ids
                )
            elif status_filter == 'expired':
                # 已过期优惠券：未使用但已过期
                # 注意：如果数据库中的状态是available，即使日期过期了也应当保持available
                queryset = queryset.filter(
                    Q(status='expired') |
                    (Q(status='available') & Q(coupon__end_date__lte=now))
                )
        else:
            # 默认只返回可用的优惠券（包括已退还的）
            returned_coupon_ids = CouponUsageRecord.objects.filter(
                member_id=member.id,
                status='returned'
            ).values_list('coupon_id', flat=True)
            
            # 查询状态为available且未过期的，或者已退还的
            queryset = queryset.filter(
                Q(status='available') |
                Q(coupon__id__in=returned_coupon_ids)
            )
            
        return queryset.select_related('coupon')
    
    @action(detail=False, methods=['get'])
    def raw_query(self, request):
        """使用原始SQL查询获取会员优惠券"""
        try:
            # 导入所需模块
            from django.db import connection
            from django.utils import timezone
            
            # 获取当前用户的会员ID
            try:
                member = Member.objects.get(user=request.user)
            except Member.DoesNotExist:
                return Response({'error': '会员不存在'}, status=status.HTTP_404_NOT_FOUND)
            
            # 获取请求中指定的status过滤参数
            request_status = request.query_params.get('status')
            print(f"请求的优惠券状态过滤: {request_status}")
            
            # 获取原始优惠券中状态为inactive的优惠券代码
            inactive_coupon_codes = []
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT code FROM coupon_coupon 
                    WHERE status = 'inactive'
                """)
                rows = cursor.fetchall()
                if rows:
                    inactive_coupon_codes = [f"'{row[0]}'" for row in rows]
            
            # 构建用于SQL中的IN子句
            inactive_codes_str = ", ".join(inactive_coupon_codes) if inactive_coupon_codes else "''"
            
            # 构建SQL查询条件，根据请求的状态过滤
            status_condition = ""
            if request_status:
                if request_status == 'used':
                    status_condition = " AND mc.status = 'used'"
                elif request_status == 'available':
                    status_condition = " AND mc.status = 'available'"
                elif request_status == 'expired':
                    status_condition = " AND mc.status = 'expired'"
            
            # 使用原始SQL查询，排除inactive状态的优惠券
            with connection.cursor() as cursor:
                query = f"""
                    SELECT 
                        mc.id, mc.member_id, mc.coupon_id, mc.used_at, mc.order_id, mc.created_at,
                        mc.status, 
                        c.name, c.code, c.type, c.value, c.min_amount, 
                        c.max_discount, c.start_date, c.end_date, c.is_active
                    FROM 
                        member_membercoupon mc
                    JOIN 
                        member_coupon c ON mc.coupon_id = c.id
                    WHERE 
                        mc.member_id = %s
                    AND
                        c.code NOT IN ({inactive_codes_str if inactive_coupon_codes else "''"})
                    AND
                        mc.status != 'inactive'
                    {status_condition}
                    ORDER BY 
                        mc.created_at DESC
                """
                
                print(f"执行SQL查询: {query}")
                cursor.execute(query, [member.id])
                
                columns = [col[0] for col in cursor.description]
                coupons = []
                
                for row in cursor.fetchall():
                    coupon_dict = dict(zip(columns, row))
                    
                    # 计算状态
                    now = timezone.now()
                    
                    # 确保日期时间使用相同的时区格式
                    end_date = coupon_dict['end_date']
                    if end_date and not timezone.is_aware(end_date):
                        end_date = timezone.make_aware(end_date)
                    
                    # 初始化status变量，确保始终有定义
                    db_status = coupon_dict['status']
                    current_status = db_status  # 预设当前状态为数据库状态
                    
                    # 优先使用数据库中的status字段，计算真实状态
                    if db_status == 'used':
                        current_status = 'used'
                    elif db_status == 'available' and coupon_dict['used_at']:
                        # 如果状态为available但used_at不为空，说明优惠券已被退还
                        current_status = 'available'
                    elif db_status == 'available':
                        # 保持状态为available，即使过期时间已过，因为后端是权威来源
                        current_status = 'available'
                    else:
                        current_status = db_status or 'available'
                        
                    # 检查是否需要更新优惠券的过期状态（仅用于前端显示）
                    # 如果数据库中记录的状态不是expired，但日期确实已过期，则标记为expired（除非是used状态）
                    if current_status != 'expired' and current_status != 'used' and end_date and end_date < now:
                        # 这里不更改数据库状态，但在API响应中返回expired以便前端正确显示
                        current_status = 'expired'
                    
                    # 如果请求指定了状态过滤，已经在SQL中进行过滤，这里只需额外检查计算得出的状态
                    # 比如SQL中是available状态，但计算后可能变成expired状态
                    if request_status and current_status != request_status and request_status != 'all':
                        # 仍然不匹配，跳过
                        continue
                    
                    # 构建与API一致的结构
                    formatted_coupon = {
                        'id': coupon_dict['id'],
                        'member': coupon_dict['member_id'],
                        'used_at': coupon_dict['used_at'],
                        'order_id': coupon_dict['order_id'],
                        'status': current_status,  # 使用计算后的状态
                        'coupon_detail': {
                            'id': coupon_dict['coupon_id'],
                            'name': coupon_dict['name'],
                            'code': coupon_dict['code'],
                            'type': coupon_dict['type'],
                            'value': float(coupon_dict['value']),
                            'min_amount': float(coupon_dict['min_amount']),
                            'max_discount': float(coupon_dict['max_discount']) if coupon_dict['max_discount'] else None,
                            'start_date': coupon_dict['start_date'],
                            'end_date': end_date
                        }
                    }
                    
                    coupons.append(formatted_coupon)
                
                print(f"查询结果数量: {len(coupons)}, 状态过滤: {request_status}")
                return Response(coupons)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': f'获取优惠券失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """使用优惠券"""
        try:
            member_coupon = self.get_object()
            order_id = request.data.get('order_id')
            
            if not order_id:
                return Response({'error': '缺少订单ID'}, status=status.HTTP_400_BAD_REQUEST)
                
            # 检查优惠券是否可用
            if member_coupon.status != 'available':
                return Response({'error': '优惠券状态不可用'}, status=status.HTTP_400_BAD_REQUEST)
                
            # 检查优惠券是否过期
            now = timezone.now()
            if member_coupon.coupon.end_date < now:
                return Response({'error': '优惠券已过期'}, status=status.HTTP_400_BAD_REQUEST)
                
            # 检查原始优惠券状态
            try:
                original_coupon = Coupon.objects.filter(code=member_coupon.coupon.code).first()
                if original_coupon and original_coupon.status != 'active':
                    return Response({'error': '该优惠券已被禁用'}, status=status.HTTP_400_BAD_REQUEST)
            except:
                pass
                
            # 更新优惠券状态
            member_coupon.status = 'used'
            member_coupon.used_at = now
            member_coupon.order_id = order_id
            member_coupon.save()
            
            # 创建使用记录
            try:
                member = member_coupon.member
                coupon = member_coupon.coupon
                
                # 根据优惠券类型确定折扣金额
                discount_amount = 0
                if coupon.type == 'fixed':
                    discount_amount = float(coupon.value)
                elif coupon.type == 'discount':
                    # 这里需要从订单获取总金额来计算折扣
                    # 暂时用一个固定值代替
                    discount_amount = float(coupon.value)
                elif coupon.type == 'free_shipping':
                    discount_amount = 10  # 默认运费10元
                
                # 创建使用记录
                usage_record = CouponUsageRecord(
                    member_id=member.id,
                    coupon_id=original_coupon.id if original_coupon else coupon.id,
                    order_id=order_id,
                    coupon_code=coupon.code,
                    coupon_type=coupon.type,
                    discount_amount=discount_amount,
                    status='used'
                )
                usage_record.save()
            except Exception as e:
                print(f"创建优惠券使用记录失败: {e}")
                
            return Response({'success': True, 'message': '优惠券使用成功'})
            
        except Exception as e:
            return Response({'error': f'使用优惠券失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CouponUsageRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CouponUsageRecordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """获取当前会员的优惠券使用记录"""
        try:
            member = Member.objects.get(user=self.request.user)
            return CouponUsageRecord.objects.filter(member_id=member.id).order_by('-used_at')
        except:
            return CouponUsageRecord.objects.none()