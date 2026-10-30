from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('processing', '处理中'),
        ('shipped', '已发货'),
        ('delivered', '已送达'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
        ('refunding', '退款中'),
        ('refunded', '已退款'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('alipay', '支付宝'),
        ('wechat', '微信支付'),
        ('bank_card', '银行卡'),
        ('balance', '余额支付'),
        ('cod', '货到付款'),
    ]
    
    # 基本信息
    order_number = models.CharField(max_length=50, unique=True, help_text='订单号')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # 价格信息
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text='商品小计')
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text='运费')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text='优惠券优惠金额')
    member_discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text='会员折扣金额')
    member_level = models.CharField(max_length=50, null=True, blank=True, help_text='下单时的会员等级')
    member_discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.00'), help_text='会员折扣率')
    
    # 支付信息
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    payment_status = models.CharField(max_length=20, blank=True, null=True, help_text='支付状态')
    
    # 收货信息
    shipping_address = models.JSONField(help_text='收货地址')
    
    # 备注信息
    remark = models.TextField(blank=True, null=True, help_text='订单备注')
    
    # 元数据，存储优惠券ID等额外信息
    meta = models.JSONField(default=dict, blank=True, null=True, help_text='元数据，存储优惠券等额外信息')
    
    # 支付信息扩展字段
    paid_at = models.DateTimeField(null=True, blank=True, help_text='支付时间')
    payment_transaction_id = models.CharField(max_length=100, null=True, blank=True, help_text='支付交易号')
    
    # 时间信息
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '订单'
        verbose_name_plural = '订单'
        ordering = ['-created_at']
        db_table = 'order_order'
    
    def __str__(self):
        return f'订单 {self.order_number}'
    
    @property
    def can_cancel(self):
        """是否可以取消"""
        return self.status in ['pending', 'paid']
    
    @property
    def can_pay(self):
        """是否可以支付"""
        return self.status == 'pending'
    
    @property
    def can_confirm_receipt(self):
        """是否可以确认收货"""
        return self.status == 'delivered'
    
    @property
    def total_price(self):
        """计算总价（包含会员折扣和优惠券折扣）"""
        return self.total_amount + self.shipping_fee - self.discount_amount - self.member_discount
    
    @property
    def can_request_after_sale(self):
        """是否可以申请售后"""
        return self.status in ['completed', 'delivered']
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_str = str(uuid.uuid4()).replace('-', '')[:8]
            self.order_number = f'ORD{timestamp}{random_str}'
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_variant = models.ForeignKey('product.ProductVariant', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200, help_text='商品名称')
    variant_name = models.CharField(max_length=100, help_text='变体名称')
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text='价格')
    quantity = models.IntegerField(help_text='数量')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, help_text='小计')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = '订单商品'
        verbose_name_plural = '订单商品'
        db_table = 'order_orderitem'
    
    def __str__(self):
        return f'{self.product_name} x {self.quantity}'
    
    def save(self, *args, **kwargs):
        if isinstance(self.price, (int, float)) and isinstance(self.quantity, (int, float)):
            self.subtotal = Decimal(str(float(self.price) * float(self.quantity)))
        super().save(*args, **kwargs)

class OrderStatusHistory(models.Model):
    """订单状态变更历史"""
    order = models.ForeignKey(Order, related_name='status_history', on_delete=models.CASCADE)
    from_status = models.CharField(max_length=20, blank=True, help_text='原状态')
    to_status = models.CharField(max_length=20, help_text='新状态')
    remark = models.TextField(blank=True, help_text='备注')
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text='操作人')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = '订单状态历史'
        verbose_name_plural = '订单状态历史'
        ordering = ['-created_at']
        db_table = 'order_orderstatushistory'
    
    def __str__(self):
        return f'{self.order.order_number}: {self.from_status} -> {self.to_status}'

class OrderRefund(models.Model):
    """订单退款"""
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('approved', '已同意'),
        ('rejected', '已拒绝'),
        ('processing', '处理中'),
        ('completed', '已完成'),
    ]
    
    TYPE_CHOICES = [
        ('refund_only', '仅退款'),
        ('return_refund', '退货退款'),
    ]
    
    order = models.ForeignKey(Order, related_name='refunds', on_delete=models.CASCADE)
    refund_number = models.CharField(max_length=32, unique=True, help_text='退款单号')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, help_text='退款类型')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(help_text='退款原因')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text='退款金额')
    evidence_images = models.JSONField(default=list, blank=True, help_text='证据图片')
    admin_remark = models.TextField(blank=True, help_text='管理员备注')
    processed_at = models.DateTimeField(null=True, blank=True, help_text='处理时间')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # 优惠券退还相关字段
    coupon_returned = models.BooleanField(default=False, help_text='是否已退还优惠券')
    coupon_returned_at = models.DateTimeField(null=True, blank=True, help_text='优惠券退还时间')
    coupon_code = models.CharField(max_length=50, blank=True, null=True, help_text='退还的优惠券代码')
    coupon_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='优惠券价值')
    coupon_type = models.CharField(max_length=20, blank=True, null=True, help_text='优惠券类型')
    coupon_min_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='优惠券最低消费金额')
    coupon_id = models.IntegerField(null=True, blank=True, help_text='优惠券ID')
    coupon_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='优惠券折扣金额')
    
    class Meta:
        verbose_name = '订单退款'
        verbose_name_plural = '订单退款'
        ordering = ['-created_at']
        db_table = 'order_orderrefund'
    
    def __str__(self):
        return f'退款单 {self.refund_number}'
    
    def save(self, *args, **kwargs):
        if not self.refund_number:
            import uuid
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_str = str(uuid.uuid4()).replace('-', '')[:8]
            self.refund_number = f'REF{timestamp}{random_str}'
        super().save(*args, **kwargs)