from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.utils import timezone
import re

class Role(models.Model):
    """管理员角色模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='角色名称')
    description = models.TextField(blank=True, verbose_name='角色描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '管理员角色'
        verbose_name_plural = '管理员角色'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.description}"
    
    @property 
    def permission_count(self):
        """获取角色拥有的权限数量"""
        return self.permissions.count()

class AdminUser(models.Model):
    """管理员用户模型"""
    username = models.CharField(max_length=150, unique=True, verbose_name='用户名')
    password = models.CharField(max_length=128, verbose_name='密码')
    email = models.EmailField(blank=True, null=True, verbose_name='邮箱')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='手机号')
    real_name = models.CharField(max_length=50, blank=True, verbose_name='真实姓名')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, verbose_name='角色')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='最后登录时间')
    login_count = models.PositiveIntegerField(default=0, verbose_name='登录次数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '管理员用户'
        verbose_name_plural = '管理员用户'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.real_name or '未设置姓名'})"
    
    def clean(self):
        """数据验证"""
        super().clean()
        # 验证用户名格式
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', self.username):
            raise ValidationError({'username': '用户名只能包含字母、数字和下划线，长度3-20位'})
        
        # 验证手机号格式
        if self.phone and not re.match(r'^1[3-9]\d{9}$', self.phone):
            raise ValidationError({'phone': '请输入正确的手机号格式'})
    
    def set_password(self, raw_password):
        """设置密码（加密存储）"""
        # 密码强度验证
        if len(raw_password) < 8:
            raise ValidationError('密码长度至少8位')
        if not re.search(r'[A-Za-z]', raw_password):
            raise ValidationError('密码必须包含字母')
        if not re.search(r'\d', raw_password):
            raise ValidationError('密码必须包含数字')
        
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """验证密码"""
        return check_password(raw_password, self.password)
    
    def update_login_info(self):
        """更新登录信息"""
        self.last_login = timezone.now()
        self.login_count += 1
        self.save(update_fields=['last_login', 'login_count'])
    
    def has_permission(self, permission_codename):
        """检查是否拥有指定权限"""
        if not self.is_active or not self.role or not self.role.is_active:
            return False
        return self.role.permissions.filter(codename=permission_codename, is_active=True).exists()
    
    @property
    def role_name(self):
        """获取角色名称"""
        return self.role.name if self.role else '无角色'

class Permission(models.Model):
    """权限模型"""
    name = models.CharField(max_length=100, verbose_name='权限名称')
    codename = models.CharField(max_length=100, unique=True, verbose_name='权限代码')
    description = models.TextField(blank=True, verbose_name='权限描述')
    module = models.CharField(max_length=50, default='system', verbose_name='所属模块')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    roles = models.ManyToManyField(Role, related_name='permissions', blank=True, verbose_name='关联角色')
    
    class Meta:
        verbose_name = '系统权限'
        verbose_name_plural = '系统权限'
        ordering = ['module', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.codename})"
    
    def clean(self):
        """数据验证"""
        super().clean()
        # 验证权限代码格式
        if not re.match(r'^[a-z_]+$', self.codename):
            raise ValidationError({'codename': '权限代码只能包含小写字母和下划线'})
    
    @property
    def role_count(self):
        """获取拥有此权限的角色数量"""
        return self.roles.filter(is_active=True).count()