from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    """商品分类"""
    name = models.CharField(max_length=100, verbose_name='分类名称')
    description = models.TextField(blank=True, null=True, verbose_name='分类描述')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, 
                              related_name='children', verbose_name='父分类')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'product_category'
        verbose_name = '商品分类'
        verbose_name_plural = '商品分类'
        ordering = ['sort_order', 'id']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """商品信息"""
    STATUS_CHOICES = [
        ('active', '上架'),
        ('inactive', '下架'),
        ('deleted', '删除')
    ]

    name = models.CharField(max_length=200, verbose_name='商品名称')
    description = models.TextField(blank=True, null=True, verbose_name='商品描述')
    category = models.ForeignKey(Category, on_delete=models.RESTRICT, verbose_name='商品分类')
    brand = models.CharField(max_length=100, blank=True, null=True, verbose_name='品牌')
    image = models.CharField(max_length=200, blank=True, null=True, verbose_name='主图')
    images = models.JSONField(blank=True, null=True, verbose_name='图片集')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    is_featured = models.BooleanField(default=False, verbose_name='是否推荐')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name='评分')
    sales_count = models.IntegerField(default=0, verbose_name='销量')
    view_count = models.IntegerField(default=0, verbose_name='浏览量')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='基础价格')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'product_product'
        verbose_name = '商品'
        verbose_name_plural = '商品'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def price_range(self):
        """获取商品价格区间"""
        variants = self.variants.filter(is_active=True)
        if not variants.exists():
            return {'min': 0, 'max': 0}
        
        min_price = variants.order_by('price').first().price
        max_price = variants.order_by('-price').first().price
        
        return {'min': min_price, 'max': max_price}

class ProductVariant(models.Model):
    """商品变体，如不同颜色、规格等"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name='商品')
    name = models.CharField(max_length=100, verbose_name='变体名称')
    sku = models.CharField(max_length=100, unique=True, verbose_name='SKU')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格')
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='原价')
    stock = models.IntegerField(default=0, verbose_name='库存')
    weight = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True, verbose_name='重量(kg)')
    attributes = models.JSONField(blank=True, null=True, verbose_name='属性')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'product_productvariant'
        verbose_name = '商品变体'
        verbose_name_plural = '商品变体'
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    @property
    def is_on_sale(self):
        """是否特价"""
        return self.original_price and self.price < self.original_price
    
    @property
    def discount_percentage(self):
        """折扣百分比"""
        if not self.is_on_sale or not self.original_price:
            return 0
        return round((1 - self.price / self.original_price) * 100) 