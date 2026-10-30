from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Role, AdminUser, Permission

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """角色管理"""
    list_display = ('id', 'name', 'description', 'permission_display', 'is_active_display', 'created_at_local')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
# 注释掉filter_horizontal，因为permissions字段在Permission模型中
    readonly_fields = ('created_at', 'permission_count')
    ordering = ('name',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'description', 'is_active')
        }),
        # ('权限配置', {
        #     'fields': ('permissions',),
        #     'description': '为角色分配相应的权限'
        # }),
        ('统计信息', {
            'fields': ('permission_count', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def permission_display(self, obj):
        """显示权限数量"""
        count = obj.permission_count
        if count > 0:
            return format_html(
                '<span style="color: green;">{}个权限</span>',
                count
            )
        return format_html('<span style="color: gray;">无权限</span>')
    permission_display.short_description = '权限数量'
    permission_display.admin_order_field = 'permission_count'
    
    def is_active_display(self, obj):
        """显示状态"""
        if obj.is_active:
            return format_html(
                '<span style="color: green;">✓ 启用</span>'
            )
        return format_html(
            '<span style="color: red;">✗ 禁用</span>'
        )
    is_active_display.short_description = '状态'
    is_active_display.admin_order_field = 'is_active'
    
    def created_at_local(self, obj):
        """显示本地创建时间"""
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            return local_time.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    created_at_local.short_description = '创建时间'
    created_at_local.admin_order_field = 'created_at'
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).prefetch_related('permissions')
    
    actions = ['enable_roles', 'disable_roles']
    
    def enable_roles(self, request, queryset):
        """批量启用角色"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'成功启用了 {updated} 个角色')
    enable_roles.short_description = '启用选中的角色'
    
    def disable_roles(self, request, queryset):
        """批量禁用角色"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'成功禁用了 {updated} 个角色')
    disable_roles.short_description = '禁用选中的角色'

@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    """管理员用户管理"""
    list_display = (
        'id', 'username', 'real_name', 'email', 'phone', 
        'role_display', 'is_active_display', 'last_login', 'login_count'
    )
    list_filter = ('is_active', 'role', 'created_at', 'last_login')
    search_fields = ('username', 'real_name', 'email', 'phone')
    readonly_fields = ('last_login', 'login_count', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('username', 'real_name', 'email', 'phone')
        }),
        ('密码设置', {
            'fields': ('password',),
            'description': '密码将自动加密存储。修改时请输入明文密码。'
        }),
        ('角色与权限', {
            'fields': ('role', 'is_active')
        }),
        ('登录统计', {
            'fields': ('last_login', 'login_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def role_display(self, obj):
        """显示角色"""
        if obj.role:
            color = 'green' if obj.role.is_active else 'orange'
            return format_html(
                '<span style="color: {};">{}</span>',
                color, obj.role.name
            )
        return format_html('<span style="color: gray;">未分配角色</span>')
    role_display.short_description = '角色'
    role_display.admin_order_field = 'role__name'
    
    def is_active_display(self, obj):
        """显示状态"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ 启用</span>')
        return format_html('<span style="color: red;">✗ 禁用</span>')
    is_active_display.short_description = '状态'
    is_active_display.admin_order_field = 'is_active'
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related('role')
    
    def save_model(self, request, obj, form, change):
        """保存时处理密码加密"""
        if 'password' in form.changed_data:
            try:
                # 如果密码字段被修改，进行加密
                obj.set_password(form.cleaned_data['password'])
                super().save_model(request, obj, form, change)
                messages.success(request, f'用户 {obj.username} 保存成功，密码已加密')
            except ValidationError as e:
                messages.error(request, f'密码设置失败：{e}')
        else:
            super().save_model(request, obj, form, change)
    
    actions = ['enable_users', 'disable_users', 'reset_login_count']
    
    def enable_users(self, request, queryset):
        """批量启用用户"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'成功启用了 {updated} 个用户')
    enable_users.short_description = '启用选中的用户'
    
    def disable_users(self, request, queryset):
        """批量禁用用户"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'成功禁用了 {updated} 个用户')
    disable_users.short_description = '禁用选中的用户'
    
    def reset_login_count(self, request, queryset):
        """重置登录次数"""
        updated = queryset.update(login_count=0)
        self.message_user(request, f'成功重置了 {updated} 个用户的登录次数')
    reset_login_count.short_description = '重置登录次数'

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """权限管理"""
    list_display = ('id', 'name', 'codename', 'module', 'role_count_display', 'is_active_display', 'created_at')
    list_filter = ('module', 'is_active', 'created_at')
    search_fields = ('name', 'codename', 'description')
    readonly_fields = ('created_at', 'role_count')
    ordering = ('module', 'name')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'codename', 'description', 'module', 'is_active')
        }),
        ('关联信息', {
            'fields': ('roles',),
            'description': '该权限关联的角色'
        }),
        ('统计信息', {
            'fields': ('role_count', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('roles',)
    
    def role_count_display(self, obj):
        """显示角色数量"""
        count = obj.role_count
        if count > 0:
            return format_html(
                '<span style="color: green;">{} 个角色</span>',
                count
            )
        return format_html('<span style="color: gray;">未分配</span>')
    role_count_display.short_description = '分配给角色数'
    role_count_display.admin_order_field = 'role_count'
    
    def is_active_display(self, obj):
        """显示状态"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ 启用</span>')
        return format_html('<span style="color: red;">✗ 禁用</span>')
    is_active_display.short_description = '状态'
    is_active_display.admin_order_field = 'is_active'
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).prefetch_related('roles')
    
    actions = ['enable_permissions', 'disable_permissions']
    
    def enable_permissions(self, request, queryset):
        """批量启用权限"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'成功启用了 {updated} 个权限')
    enable_permissions.short_description = '启用选中的权限'
    
    def disable_permissions(self, request, queryset):
        """批量禁用权限"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'成功禁用了 {updated} 个权限')
    disable_permissions.short_description = '禁用选中的权限'

# 自定义Admin站点标题
admin.site.site_header = '武汉精品商城管理系统'
admin.site.site_title = '武汉精品商城'
admin.site.index_title = '武汉精品商城管理后台'