from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class MemberLevel(models.Model):
    """会员等级模型"""
    name = models.CharField(max_length=50, verbose_name='等级名称', unique=True)
    points_threshold = models.IntegerField(default=0, verbose_name='升级所需积分')
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.00'), verbose_name='折扣率')
    icon = models.CharField(max_length=200, null=True, blank=True, verbose_name='等级图标')
    description = models.CharField(max_length=500, null=True, blank=True, verbose_name='等级描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'member_level'
        verbose_name = '会员等级'
        verbose_name_plural = '会员等级'
        ordering = ['points_threshold']
    
    def __str__(self):
        return f"{self.name} (积分:{self.points_threshold})"

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='手机号')
    avatar = models.CharField(max_length=200, null=True, blank=True, verbose_name='头像URL')
    gender = models.CharField(max_length=10, default='unknown', verbose_name='性别')
    birthday = models.DateField(null=True, blank=True, verbose_name='生日')
    level = models.CharField(max_length=20, default='bronze', verbose_name='会员等级')
    points = models.IntegerField(default=0, verbose_name='积分')
    growth_value = models.IntegerField(default=0, verbose_name='成长值')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='账户余额')
    total_orders = models.IntegerField(default=0, verbose_name='总订单数')
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='总消费金额')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'member_member'
        verbose_name = '会员'
        verbose_name_plural = '会员'
    
    def __str__(self):
        return f"{self.user.username}"
    
    def update_level(self):
        """根据积分更新会员等级"""
        from django.db.models import F
        
        # 获取所有可用的会员等级，按积分阈值升序排序
        levels = MemberLevel.objects.filter(is_active=True).order_by('points_threshold')
        
        # 找到用户积分满足条件的最高等级
        new_level = '银卡会员'  # 默认等级，使用中文名称
        for level in levels:
            if self.points >= level.points_threshold:
                new_level = level.name
        
        # 如果等级变化，保存并记录
        if new_level != self.level:
            old_level = self.level
            self.level = new_level
            self.save(update_fields=['level', 'updated_at'])
            return True, old_level, new_level
        
        return False, self.level, self.level

class PointsHistory(models.Model):
    """积分变动记录表"""
    TYPE_CHOICES = [
        ('order_complete', '订单完成'),
        ('order_refund', '订单退款'),
        ('admin_adjust', '管理员调整'),
        ('other', '其他')
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='points_history', verbose_name='会员')
    order_id = models.IntegerField(null=True, blank=True, verbose_name='关联订单')
    points = models.IntegerField(verbose_name='积分变动值')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='变动类型')
    description = models.CharField(max_length=200, null=True, blank=True, verbose_name='变动描述')
    admin_id = models.IntegerField(null=True, blank=True, verbose_name='管理员ID')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'member_points_history'
        verbose_name = '积分变动记录'
        verbose_name_plural = '积分变动记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.member} - {self.points}积分 - {self.get_type_display()}"

class Address(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='addresses', db_column='member_id')
    name = models.CharField(max_length=50, help_text='收货人姓名')
    phone = models.CharField(max_length=20, help_text='收货人电话')
    province = models.CharField(max_length=50, help_text='省份')
    city = models.CharField(max_length=50, help_text='城市')
    district = models.CharField(max_length=50, help_text='区县')
    detail = models.CharField(max_length=200, help_text='详细地址')
    is_default = models.BooleanField(default=False, help_text='是否为默认地址')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '收货地址'
        verbose_name_plural = '收货地址'
        ordering = ['-is_default', '-updated_at']
        db_table = 'member_address'
    
    def __str__(self):
        return f'{self.name} - {self.province}{self.city}{self.district}'
    
    def save(self, *args, **kwargs):
        # 如果设置为默认地址，将其他地址设为非默认
        if self.is_default:
            Address.objects.filter(member=self.member, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

class Coupon(models.Model):
    TYPE_CHOICES = [
        ('fixed', '满减券'),
        ('discount', '折扣券'),
        ('free_shipping', '包邮券'),
    ]
    
    STATUS_CHOICES = [
        ('active', '有效'),
        ('inactive', '无效'),
        ('expired', '已过期'),
    ]
    
    name = models.CharField(max_length=100, help_text='优惠券名称')
    code = models.CharField(max_length=20, unique=True, help_text='优惠券代码')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2, help_text='优惠金额或折扣率')
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text='最低消费金额')
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='最大优惠金额（折扣券）')
    usage_limit = models.IntegerField(default=1, help_text='使用次数限制')
    used_count = models.IntegerField(default=0, help_text='已使用次数')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(help_text='开始时间')
    end_date = models.DateTimeField(help_text='结束时间')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = '优惠券'
        verbose_name_plural = '优惠券'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.name} - {self.code}'
    
    @property
    def is_available(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.status == 'active' and
            self.start_date <= now <= self.end_date and
            self.used_count < self.usage_limit
        )

class MemberCoupon(models.Model):
    STATUS_CHOICES = [
        ('available', '可用'),
        ('used', '已使用'),
        ('expired', '已过期'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='member_coupons')
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    obtained_at = models.DateTimeField(auto_now_add=True, help_text='获得时间')
    used_at = models.DateTimeField(null=True, blank=True, help_text='使用时间')
    order_id = models.IntegerField(null=True, blank=True, help_text='使用的订单ID')
    
    class Meta:
        verbose_name = '会员优惠券'
        verbose_name_plural = '会员优惠券'
        unique_together = ['member', 'coupon']
        ordering = ['-obtained_at']
    
    def __str__(self):
        return f'{self.member.user.username} - {self.coupon.name}'
    
    @property
    def is_available(self):
        from django.utils import timezone
        return (
            self.status == 'available' and
            self.coupon.is_available and
            self.coupon.end_date >= timezone.now()
        )

class SignInRecord(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='sign_in_records')
    sign_in_date = models.DateField(auto_now_add=True)
    points_earned = models.IntegerField(default=10, help_text='签到获得积分')
    consecutive_days = models.IntegerField(default=1, help_text='连续签到天数')
    
    class Meta:
        verbose_name = '签到记录'
        verbose_name_plural = '签到记录'
        unique_together = ['member', 'sign_in_date']
        ordering = ['-sign_in_date']
    
    def __str__(self):
        return f'{self.member.user.username} - {self.sign_in_date}'

class RechargeRecord(models.Model):
    """余额充值记录模型"""
    STATUS_CHOICES = [
        ('pending', '处理中'),
        ('success', '充值成功'),
        ('failed', '充值失败'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='recharge_records', verbose_name='会员')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='充值金额')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    payment_method = models.CharField(max_length=50, default='online', verbose_name='支付方式')
    transaction_id = models.CharField(max_length=100, null=True, blank=True, verbose_name='交易号')
    remark = models.CharField(max_length=255, null=True, blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'member_recharge_record'
        verbose_name = '充值记录'
        verbose_name_plural = '充值记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.member.user.username} - ¥{self.amount} - {self.get_status_display()}"