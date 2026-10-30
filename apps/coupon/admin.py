from django.contrib import admin
from .models import Coupon, CouponUsageRecord
from apps.member.models import MemberCoupon
from django.utils import timezone
from django.contrib import messages
from django.db import connection

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'coupon_type', 'discount_amount', 'discount_rate', 'min_purchase_amount', 'start_time', 'end_time', 'is_platform', 'status']
    search_fields = ['code']
    list_filter = ['coupon_type', 'is_platform', 'status']
    actions = ['make_active', 'make_inactive']
    
    def make_active(self, request, queryset):
        """将选中的优惠券设为有效"""
        updated = queryset.update(status='active')
        
        # 同步更新member_coupon表中对应的优惠券状态
        coupon_codes = list(queryset.values_list('code', flat=True))
        if coupon_codes:
            from apps.member.models import Coupon as MemberCoupon_Coupon
            MemberCoupon_Coupon.objects.filter(code__in=coupon_codes).update(status='active')
            
        self.message_user(request, f'成功将 {updated} 张优惠券状态设为有效')
    
    make_active.short_description = "将选中的优惠券设为有效"
    
    def make_inactive(self, request, queryset):
        """将选中的优惠券设为无效"""
        updated = queryset.update(status='inactive')
        
        # 同步更新member_coupon表中对应的优惠券状态
        coupon_codes = list(queryset.values_list('code', flat=True))
        if coupon_codes:
            from apps.member.models import Coupon as MemberCoupon_Coupon
            MemberCoupon_Coupon.objects.filter(code__in=coupon_codes).update(status='inactive')
            
        self.message_user(request, f'成功将 {updated} 张优惠券状态设为无效')
    
    make_inactive.short_description = "将选中的优惠券设为无效"

@admin.register(CouponUsageRecord)
class CouponUsageRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'member_name', 'coupon_code', 'coupon_type', 'discount_amount', 'used_at', 'status', 'order_number']
    search_fields = ['coupon_code', 'member_id']
    list_filter = ['status', 'coupon_type']
    readonly_fields = ['used_at']
    actions = ['mark_as_returned']
    
    def save_model(self, request, obj, form, change):
        """重写保存方法，处理状态变更"""
        old_status = None
        if change and obj.id:
            try:
                old_obj = CouponUsageRecord.objects.get(id=obj.id)
                old_status = old_obj.status
            except:
                pass
        
        # 保存优惠券使用记录
        super().save_model(request, obj, form, change)
        
        # 如果状态从used改为returned，同步更新会员优惠券状态
        if old_status == 'used' and obj.status == 'returned':
            self._sync_member_coupon_status(obj, request)
    
    def _sync_member_coupon_status(self, obj, request):
        """同步会员优惠券状态"""
        try:
            # 查找对应的会员优惠券记录
            member_coupons = MemberCoupon.objects.filter(
                member_id=obj.member_id,
                coupon__code=obj.coupon_code
            )
            
            if not member_coupons.exists():
                messages.warning(request, f"未找到会员ID {obj.member_id} 对应的优惠券记录")
                return
            
            # 更新会员优惠券状态
            for member_coupon in member_coupons:
                member_coupon.status = 'available'
                member_coupon.used_at = None
                member_coupon.order_id = None
                member_coupon.save()
            
            # 设置退还时间
            if not obj.returned_at:
                obj.returned_at = timezone.now()
                obj.save(update_fields=['returned_at'])
            
            messages.success(request, f"已成功将优惠券 {obj.coupon_code} 退还给会员")
        except Exception as e:
            messages.error(request, f"同步会员优惠券状态失败: {str(e)}")
    
    def mark_as_returned(self, request, queryset):
        """将选中的优惠券标记为已退还"""
        count = 0
        for record in queryset:
            if record.status == 'used':
                record.status = 'returned'
                record.returned_at = timezone.now()
                record.save()
                self._sync_member_coupon_status(record, request)
                count += 1
        
        messages.success(request, f"成功将 {count} 张优惠券标记为已退还")
    
    mark_as_returned.short_description = "将选中的优惠券标记为已退还"