from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import PasswordResetRequest

@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'username', 'email', 'phone', 'status_display', 
        'matched_user_display', 'created_at', 'processed_at'
    ]
    list_filter = ['status', 'created_at', 'processed_at']
    search_fields = ['username', 'email', 'phone', 'first_name', 'last_name']
    readonly_fields = [
        'created_at', 'updated_at', 'client_ip', 'user_agent',
        'matched_user_display', 'find_user_info'
    ]
    
    fieldsets = (
        ('用户提交信息', {
            'fields': (
                ('username', 'phone'),
                ('email',),
                ('first_name', 'last_name'),
                'reason',
                'new_password',
            )
        }),
        ('系统匹配信息', {
            'fields': (
                'find_user_info',
                'matched_user_display',
            )
        }),
        ('处理信息', {
            'fields': (
                'status',
                'admin_notes',
                'processed_by',
                'processed_at',
            )
        }),
        ('技术信息', {
            'fields': (
                'created_at',
                'updated_at',
                'client_ip',
                'user_agent',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_and_reset', 'reject_request', 'find_matching_users']
    
    def status_display(self, obj):
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'rejected': '#dc3545',
            'completed': '#17a2b8'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = '状态'
    
    def matched_user_display(self, obj):
        if obj.matched_user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/" target="_blank">{}</a>',
                obj.matched_user.id,
                obj.matched_user.username
            )
        else:
            # 尝试查找匹配用户
            user = obj.find_matching_user()
            if user:
                return format_html(
                    '<span style="color: orange;">找到匹配: <a href="/admin/auth/user/{}/change/" target="_blank">{}</a></span>',
                    user.id,
                    user.username
                )
            else:
                return format_html('<span style="color: red;">未找到匹配用户</span>')
    matched_user_display.short_description = '匹配用户'
    
    def find_user_info(self, obj):
        """显示用户匹配信息"""
        user = obj.find_matching_user()
        if user:
            return format_html(
                '''
                <div style="background: #e8f5e8; padding: 10px; border-radius: 5px;">
                    <strong>找到匹配用户：</strong><br>
                    用户名: {}<br>
                    邮箱: {}<br>
                    姓名: {} {}<br>
                    注册时间: {}<br>
                    <a href="/admin/auth/user/{}/change/" target="_blank">查看用户详情</a>
                </div>
                ''',
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                user.id
            )
        else:
            return format_html(
                '''
                <div style="background: #ffe8e8; padding: 10px; border-radius: 5px;">
                    <strong>未找到匹配用户</strong><br>
                    请检查用户提交的信息是否正确
                </div>
                '''
            )
    find_user_info.short_description = '用户匹配信息'
    
    def approve_and_reset(self, request, queryset):
        """批准并重置密码"""
        success_count = 0
        error_messages = []
        
        for obj in queryset:
            if obj.status != 'pending':
                error_messages.append(f"请求 {obj.id} 状态不是待处理")
                continue
                
            success, message = obj.approve_and_reset_password(request.user)
            if success:
                success_count += 1
            else:
                error_messages.append(f"请求 {obj.id}: {message}")
        
        if success_count > 0:
            messages.success(request, f"成功处理 {success_count} 个密码重置请求")
        
        for error in error_messages:
            messages.error(request, error)
    
    approve_and_reset.short_description = "批准并重置密码"
    
    def reject_request(self, request, queryset):
        """拒绝请求"""
        updated = queryset.filter(status='pending').update(
            status='rejected',
            processed_by=request.user,
            admin_notes='管理员批量拒绝'
        )
        messages.success(request, f"已拒绝 {updated} 个请求")
    
    reject_request.short_description = "拒绝请求"
    
    def find_matching_users(self, request, queryset):
        """查找匹配用户"""
        for obj in queryset:
            user = obj.find_matching_user()
            if user:
                obj.matched_user = user
                obj.save()
        
        messages.success(request, "已更新匹配用户信息")
    
    find_matching_users.short_description = "查找匹配用户"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('matched_user', 'processed_by')
    
    def save_model(self, request, obj, form, change):
        # 如果状态改为已批准或已完成，且没有处理人，则设置当前用户为处理人
        if obj.status in ['approved', 'completed'] and not obj.processed_by:
            obj.processed_by = request.user
        super().save_model(request, obj, form, change)
