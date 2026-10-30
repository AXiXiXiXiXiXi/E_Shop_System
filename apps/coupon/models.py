from django.db import models
from django.utils import timezone
from apps.member.models import Member, MemberCoupon as MemberCouponBase

class Coupon(models.Model):
    COUPON_TYPE_CHOICES = [
        ('full_reduction', '满减'),
        ('discount', '折扣'),
        ('free_shipping', '包邮券'),
    ]
    
    STATUS_CHOICES = [
        ('active', '有效'),
        ('inactive', '无效'),
        ('expired', '已过期'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    coupon_type = models.CharField(max_length=20, choices=COUPON_TYPE_CHOICES)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_rate = models.FloatField(null=True, blank=True)  # 折扣率，如0.9表示9折
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # 满足条件金额
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_platform = models.BooleanField(default=True)  # 是否平台统一优惠券
    usage_limit = models.IntegerField(default=1, help_text='使用次数限制')
    used_count = models.IntegerField(default=0, help_text='已使用次数')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', help_text='优惠券状态')
    
    def is_valid(self):
        """检查优惠券是否有效"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.status == 'active'
    
    def __str__(self):
        return f"{self.get_coupon_type_display()}: {self.code}"

class CouponUsageRecord(models.Model):
    """优惠券使用记录表"""
    STATUS_CHOICES = [
        ('used', '已使用'),
        ('returned', '已退还'),
        ('expired', '已过期无法退还')
    ]
    
    member_id = models.IntegerField()
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    order_id = models.IntegerField()
    coupon_code = models.CharField(max_length=50)
    coupon_type = models.CharField(max_length=20)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='used', help_text='优惠券状态')
    returned_at = models.DateTimeField(null=True, blank=True, help_text='退还时间')
    admin_remark = models.TextField(blank=True, null=True, help_text='管理员备注')
    
    class Meta:
        db_table = 'member_couponusagerecord'
        verbose_name = '优惠券使用记录'
        verbose_name_plural = '优惠券使用记录'
        
    def __str__(self):
        return f"{self.member_id} - {self.coupon_code} - {self.used_at}"
    
    @property
    def member_name(self):
        """获取会员名称"""
        try:
            member = Member.objects.get(id=self.member_id)
            return member.user.username
        except:
            return f"会员ID: {self.member_id}"
    
    @property
    def order_number(self):
        """获取订单号"""
        try:
            from apps.order.models import Order
            order = Order.objects.get(id=self.order_id)
            return order.order_number
        except:
            return f"订单ID: {self.order_id}"