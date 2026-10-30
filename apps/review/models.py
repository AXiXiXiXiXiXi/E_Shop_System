from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.order.models import OrderItem

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')  # 用户
    product_id = models.IntegerField(help_text='商品ID')  # 使用ID替代Product外键
    product_name = models.CharField(max_length=200, help_text='商品名称', blank=True, null=True)  # 保存商品名称，可选
    rating = models.DecimalField(max_digits=2, decimal_places=1, validators=[MinValueValidator(1), MaxValueValidator(5)])  # 评分
    content = models.TextField(blank=True)  # 评价内容
    images = models.JSONField(null=True, blank=True)  # 图片URL列表
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间
    updated_at = models.DateTimeField(auto_now=True)  # 更新时间
    
    def __str__(self):
        return f"{self.user.username}对{self.product_name or f'商品{self.product_id}'}的评价"

class AfterSaleRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('completed', '已完成'),
    ]
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='after_sale_requests')  # 关联订单项
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='after_sale_requests')  # 用户
    reason = models.TextField()  # 申请原因
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    handler = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_after_sales', verbose_name='处理人员')  # 处理人员
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '售后申请'
        verbose_name_plural = '售后申请'
        
    def __str__(self):
        return f"{self.user.username}的售后申请 - {self.get_status_display()}"
    
    @property
    def can_chat(self):
        """判断是否可以聊天（未完成状态才能聊天）"""
        return self.status != 'completed'

class AfterSaleChatMessage(models.Model):
    SENDER_CHOICES = [
        ('user', '用户'),
        ('admin', '客服'),
    ]
    
    after_sale_request = models.ForeignKey(AfterSaleRequest, on_delete=models.CASCADE, related_name='chat_messages')
    sender_type = models.CharField(max_length=10, choices=SENDER_CHOICES)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)  # 是否已读
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = '售后聊天消息'
        verbose_name_plural = '售后聊天消息'
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.sender.username} ({self.get_sender_type_display()}): {self.message[:50]}..."