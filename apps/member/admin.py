from django.contrib import admin
from django.http import HttpResponseRedirect
from django.contrib import messages
from django import forms
from django.template.response import TemplateResponse
from django.contrib.admin import helpers
from .models import MemberLevel, Member, PointsHistory, Address, Coupon, MemberCoupon

@admin.register(MemberLevel)
class MemberLevelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'points_threshold', 'discount_rate', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

class AdjustPointsForm(forms.Form):
    adjustment = forms.IntegerField(label='积分调整值', required=True,
                                  help_text='输入正数增加积分，输入负数减少积分')
    reason = forms.CharField(label='调整原因', required=True, max_length=200,
                           help_text='请简要说明积分调整原因')

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'level', 'points', 'total_orders', 'total_spent', 'updated_at')
    list_filter = ('level',)
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('total_orders', 'total_spent')
    actions = ['adjust_points']
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'phone', 'avatar', 'gender', 'birthday')
        }),
        ('会员状态', {
            'fields': ('level', 'points', 'growth_value', 'balance')
        }),
        ('消费统计', {
            'fields': ('total_orders', 'total_spent')
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        在保存会员模型时，如果积分发生变化，记录历史并更新等级
        """
        if change:  # 只在编辑时处理
            # 获取原始对象
            old_instance = self.model.objects.filter(pk=obj.pk).first()
            if old_instance and old_instance.points != obj.points:
                points_change = obj.points - old_instance.points
                # 创建积分变动记录
                PointsHistory(
                    member=obj,
                    points=points_change,
                    type='admin_adjust',
                    description=f'管理员直接修改积分，从 {old_instance.points} 变为 {obj.points}',
                    admin_id=request.user.id
                ).save()
                
                # 在积分变更后触发会员等级更新
                obj.update_level()
                
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    f'已记录积分变更 ({points_change}) 并更新会员等级'
                )
        
        super().save_model(request, obj, form, change)

    def adjust_points(self, request, queryset):
        if 'apply' in request.POST:
            form = AdjustPointsForm(request.POST)
            if form.is_valid():
                adjustment = form.cleaned_data['adjustment']
                reason = form.cleaned_data['reason']
                
                count = 0
                for member in queryset:
                    old_points = member.points
                    new_points = max(0, old_points + adjustment)  # 确保积分不会变为负数
                    
                    # 更新会员积分
                    member.points = new_points
                    member.save()
                    
                    # 创建积分历史记录
                    PointsHistory(
                        member=member,
                        points=adjustment,
                        type='admin_adjust',
                        description=reason,
                        admin_id=request.user.id
                    ).save()
                    
                    # 触发会员等级更新
                    member.update_level()
                    count += 1
                
                self.message_user(
                    request,
                    f"成功为 {count} 个会员{'增加' if adjustment > 0 else '减少'} {abs(adjustment)} 积分。",
                    messages.SUCCESS
                )
                return HttpResponseRedirect(request.get_full_path())
        
        # 显示中间确认页面
        form = AdjustPointsForm()
        context = {
            'title': '调整会员积分',
            'queryset': queryset,
            'opts': self.model._meta,
            'form': form,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'media': self.media,
        }
        return TemplateResponse(request, 'admin/adjust_points_confirmation.html', context)
        
    adjust_points.short_description = '调整所选会员的积分'

@admin.register(PointsHistory)
class PointsHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'member', 'points', 'type', 'order_id', 'created_at')
    list_filter = ('type',)
    search_fields = ('member__user__username', 'description')
    # 移除date_hierarchy以避免时区问题
    # date_hierarchy = 'created_at'
    
    # 添加自定义过滤器
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('-created_at')

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'member', 'name', 'phone', 'province', 'city', 'is_default')
    list_filter = ('province', 'city', 'is_default')
    search_fields = ('name', 'phone', 'detail')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'type', 'value', 'min_amount', 'start_date', 'end_date', 'status')
    list_filter = ('type', 'status')
    search_fields = ('name', 'code')
    actions = ['make_active', 'make_inactive']
    
    def save_model(self, request, obj, form, change):
        # 保存member_coupon表的优惠券
        super().save_model(request, obj, form, change)
        
        # 同步更新coupon_coupon表中的对应记录
        if change and form.changed_data and 'status' in form.changed_data:
            from apps.coupon.models import Coupon as CouponCoupon
            try:
                coupon_obj = CouponCoupon.objects.filter(code=obj.code).first()
                if coupon_obj:
                    coupon_obj.status = obj.status
                    coupon_obj.save(update_fields=['status'])
                    messages.success(request, f"成功同步更新优惠券 {obj.code} 在coupon_coupon表中的状态为 {obj.status}")
                else:
                    messages.warning(request, f"在coupon_coupon表中未找到代码为 {obj.code} 的优惠券")
            except Exception as e:
                messages.error(request, f"同步更新coupon_coupon表失败: {str(e)}")
    
    def make_active(self, request, queryset):
        """将选中的优惠券设为有效"""
        updated = queryset.update(status='active')
        
        # 同步更新coupon_coupon表
        coupon_codes = list(queryset.values_list('code', flat=True))
        if coupon_codes:
            try:
                from apps.coupon.models import Coupon as CouponCoupon
                count = CouponCoupon.objects.filter(code__in=coupon_codes).update(status='active')
                messages.success(request, f"成功同步更新 {count} 张优惠券在coupon_coupon表中的状态")
            except Exception as e:
                messages.error(request, f"同步更新coupon_coupon表失败: {str(e)}")
                
        messages.success(request, f'成功将 {updated} 张优惠券状态设为有效')
    
    make_active.short_description = "将选中的优惠券设为有效"
    
    def make_inactive(self, request, queryset):
        """将选中的优惠券设为无效"""
        updated = queryset.update(status='inactive')
        
        # 同步更新coupon_coupon表
        coupon_codes = list(queryset.values_list('code', flat=True))
        if coupon_codes:
            try:
                from apps.coupon.models import Coupon as CouponCoupon
                count = CouponCoupon.objects.filter(code__in=coupon_codes).update(status='inactive')
                messages.success(request, f"成功同步更新 {count} 张优惠券在coupon_coupon表中的状态")
            except Exception as e:
                messages.error(request, f"同步更新coupon_coupon表失败: {str(e)}")
                
        messages.success(request, f'成功将 {updated} 张优惠券状态设为无效')
    
    make_inactive.short_description = "将选中的优惠券设为无效"

@admin.register(MemberCoupon)
class MemberCouponAdmin(admin.ModelAdmin):
    list_display = ('id', 'member', 'coupon', 'status', 'obtained_at', 'used_at')
    list_filter = ('status',)
    search_fields = ('member__user__username', 'coupon__name')