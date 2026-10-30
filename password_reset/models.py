from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class PasswordResetRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('completed', '已完成'),
    ]
    
    # 用户提交的信息
    username = models.CharField(max_length=150, verbose_name='用户名')
    phone = models.CharField(max_length=20, verbose_name='手机号')
    email = models.EmailField(verbose_name='邮箱')
    first_name = models.CharField(max_length=30, verbose_name='姓')
    last_name = models.CharField(max_length=30, verbose_name='名')
    reason = models.TextField(verbose_name='忘记密码的理由')
    new_password = models.CharField(max_length=128, verbose_name='新密码')
    
    # 系统信息
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    # 管理员处理信息
    matched_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='匹配的用户')
    admin_notes = models.TextField(blank=True, verbose_name='管理员备注')
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='processed_reset_requests',
        verbose_name='处理人'
    )
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    
    # 客户端信息
    client_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='客户端IP')
    user_agent = models.TextField(blank=True, verbose_name='用户代理')
    
    class Meta:
        verbose_name = '密码重置请求'
        verbose_name_plural = '密码重置请求'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.username} - {self.get_status_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # 更新处理时间
        if self.status in ['approved', 'rejected', 'completed'] and not self.processed_at:
            self.processed_at = timezone.now()
        super().save(*args, **kwargs)
    
    def find_matching_user(self):
        """查找匹配的用户"""
        # 首先尝试用户名精确匹配
        try:
            user = User.objects.get(username=self.username)
            return user
        except User.DoesNotExist:
            pass
        
        # 尝试邮箱匹配
        try:
            user = User.objects.get(email=self.email)
            return user
        except User.DoesNotExist:
            pass
        
        # 尝试根据姓名和邮箱的组合匹配
        users = User.objects.filter(
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email
        )
        if users.exists():
            return users.first()
        
        return None
    
    def can_approve(self):
        """检查是否可以批准此请求"""
        if self.status != 'pending':
            return False, "请求状态不是待处理"
        
        matching_user = self.find_matching_user()
        if not matching_user:
            return False, "找不到匹配的用户"
        
        return True, "可以批准"
    
    def approve_and_reset_password(self, admin_user):
        """批准请求并重置密码"""
        can_approve, message = self.can_approve()
        if not can_approve:
            return False, message
        
        matching_user = self.find_matching_user()
        if not matching_user:
            return False, "找不到匹配的用户"
        
        # 重置密码
        matching_user.set_password(self.new_password)
        matching_user.save()
        
        # 更新请求状态
        self.matched_user = matching_user
        self.status = 'completed'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.admin_notes = f"密码重置成功，用户：{matching_user.username}"
        self.save()
        
        return True, "密码重置成功"
