"""
管理员权限检查装饰器和工具类
"""
from functools import wraps
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from .models import AdminUser

def admin_permission_required(permission_codename):
    """
    管理员权限检查装饰器
    用法: @admin_permission_required('view_user')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # 检查用户是否已认证
            if not request.user.is_authenticated:
                return JsonResponse({'error': '请先登录'}, status=401)
            
            # 获取管理员用户信息
            try:
                admin_user = AdminUser.objects.get(username=request.user.username)
            except AdminUser.DoesNotExist:
                return JsonResponse({'error': '非管理员用户'}, status=403)
            
            # 检查权限
            if not admin_user.has_permission(permission_codename):
                return JsonResponse({
                    'error': f'您没有权限执行此操作，需要权限: {permission_codename}'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def admin_role_required(role_names):
    """
    管理员角色检查装饰器
    用法: @admin_role_required(['超级管理员', '系统管理员'])
    """
    if isinstance(role_names, str):
        role_names = [role_names]
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': '请先登录'}, status=401)
            
            try:
                admin_user = AdminUser.objects.get(username=request.user.username)
            except AdminUser.DoesNotExist:
                return JsonResponse({'error': '非管理员用户'}, status=403)
            
            if not admin_user.role or admin_user.role.name not in role_names:
                return JsonResponse({
                    'error': f'您的角色权限不足，需要角色: {", ".join(role_names)}'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

class AdminPermission(permissions.BasePermission):
    """
    DRF管理员权限检查类
    用法: permission_classes = [AdminPermission]
    """
    
    def has_permission(self, request, view):
        """检查基本权限"""
        if not request.user.is_authenticated:
            return False
        
        try:
            admin_user = AdminUser.objects.get(username=request.user.username)
            return admin_user.is_active and admin_user.role and admin_user.role.is_active
        except AdminUser.DoesNotExist:
            return False

class AdminPermissionRequired(permissions.BasePermission):
    """
    DRF特定权限检查类
    用法: permission_classes = [AdminPermissionRequired]
    需要在视图中设置 required_permission 属性
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # 获取视图要求的权限
        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            return True  # 如果没有设置权限要求，则允许访问
        
        try:
            admin_user = AdminUser.objects.get(username=request.user.username)
            return admin_user.has_permission(required_permission)
        except AdminUser.DoesNotExist:
            return False

class PermissionChecker:
    """权限检查工具类"""
    
    @staticmethod
    def check_admin_permission(user, permission_codename):
        """检查管理员用户是否有指定权限"""
        if not user.is_authenticated:
            return False, '用户未登录'
        
        try:
            admin_user = AdminUser.objects.get(username=user.username)
            if not admin_user.is_active:
                return False, '管理员账户已被禁用'
            
            if not admin_user.role:
                return False, '用户未分配角色'
            
            if not admin_user.role.is_active:
                return False, '用户角色已被禁用'
            
            if admin_user.has_permission(permission_codename):
                return True, '权限检查通过'
            else:
                return False, f'缺少权限: {permission_codename}'
                
        except AdminUser.DoesNotExist:
            return False, '用户不是管理员'
    
    @staticmethod
    def get_user_permissions(user):
        """获取用户所有权限"""
        try:
            admin_user = AdminUser.objects.get(username=user.username)
            if admin_user.role and admin_user.is_active and admin_user.role.is_active:
                return list(admin_user.role.permissions.filter(is_active=True).values_list('codename', flat=True))
            return []
        except AdminUser.DoesNotExist:
            return []
    
    @staticmethod
    def get_user_role(user):
        """获取用户角色信息"""
        try:
            admin_user = AdminUser.objects.get(username=user.username)
            if admin_user.role:
                return {
                    'role_name': admin_user.role.name,
                    'role_description': admin_user.role.description,
                    'is_active': admin_user.role.is_active
                }
            return None
        except AdminUser.DoesNotExist:
            return None

# 常用权限常量
class Permissions:
    """权限常量定义"""
    
    # 用户管理权限
    VIEW_USER = 'view_user'
    ADD_USER = 'add_user'
    CHANGE_USER = 'change_user'
    DELETE_USER = 'delete_user'
    
    # 角色权限管理
    VIEW_ROLE = 'view_role'
    ADD_ROLE = 'add_role'
    CHANGE_ROLE = 'change_role'
    DELETE_ROLE = 'delete_role'
    
    # 权限管理
    VIEW_PERMISSION = 'view_permission'
    ADD_PERMISSION = 'add_permission'
    CHANGE_PERMISSION = 'change_permission'
    DELETE_PERMISSION = 'delete_permission'
    
    # 订单管理权限
    VIEW_ORDER = 'view_order'
    CHANGE_ORDER = 'change_order'
    DELETE_ORDER = 'delete_order'
    
    # 产品管理权限
    VIEW_PRODUCT = 'view_product'
    ADD_PRODUCT = 'add_product'
    CHANGE_PRODUCT = 'change_product'
    DELETE_PRODUCT = 'delete_product'
    
    # 会员管理权限
    VIEW_MEMBER = 'view_member'
    CHANGE_MEMBER = 'change_member'
    ADJUST_POINTS = 'adjust_points'
    
    # 优惠券管理权限
    VIEW_COUPON = 'view_coupon'
    ADD_COUPON = 'add_coupon'
    CHANGE_COUPON = 'change_coupon'
    DELETE_COUPON = 'delete_coupon'
    
    # 系统管理权限
    SYSTEM_SETTINGS = 'system_settings'
    VIEW_LOGS = 'view_logs'
    BACKUP_DATA = 'backup_data' 