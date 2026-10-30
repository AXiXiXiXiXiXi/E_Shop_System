"""
权限装饰器
用于控制用户访问权限和学校数据隔离
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def admin_required(view_func):
    """
    管理员权限装饰器
    要求用户必须是管理员角色或超级管理员
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # 超级管理员直接放行
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # 检查是否有 profile（防止使用 createsuperuser 创建的用户）
        if not hasattr(request.user, 'profile'):
            messages.error(request, '您的账号没有关联的用户资料，请联系管理员')
            return redirect('home')
        
        # 检查是否是管理员
        if request.user.profile.role != 'admin':
            messages.error(request, '您没有权限访问此页面，需要管理员权限')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def superuser_required(view_func):
    """
    超级管理员权限装饰器
    要求用户必须是 Django superuser
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, '您没有权限访问此页面，需要超级管理员权限')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_user_school(request):
    """
    获取当前登录用户所属学校
    用于学校数据隔离
    超级管理员返回 None
    """
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return None  # 超级管理员不绑定学校
        return request.user.profile.school
    return None


def check_school_permission(user, obj):
    """
    检查用户是否有权限访问该对象
    验证对象所属学校是否与用户所属学校一致
    
    参数:
        user: 当前用户
        obj: 需要检查的对象（必须有 school 属性）
    
    返回:
        bool: True 表示有权限，False 表示无权限
    """
    if not user.is_authenticated:
        return False
    
    # 超级管理员可以访问所有数据
    if user.is_superuser:
        return True
    
    user_school = user.profile.school
    
    # 如果对象直接有 school 属性
    if hasattr(obj, 'school'):
        return obj.school == user_school
    
    # 如果对象通过外键关联到 school（如 Claim 通过 lost_item）
    if hasattr(obj, 'lost_item') and hasattr(obj.lost_item, 'school'):
        return obj.lost_item.school == user_school
    
    return False


def check_owner_permission(user, obj):
    """
    检查用户是否是对象的所有者
    
    参数:
        user: 当前用户
        obj: 需要检查的对象（必须有 publish_user 属性）
    
    返回:
        bool: True 表示是所有者，False 表示不是
    """
    if not user.is_authenticated:
        return False
    
    # 超级管理员可以操作所有数据
    if user.is_superuser:
        return True
    
    if hasattr(obj, 'publish_user'):
        return obj.publish_user == user
    
    return False

