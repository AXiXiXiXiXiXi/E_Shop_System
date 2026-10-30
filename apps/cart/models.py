from django.db import models
from django.contrib.auth.models import User
from apps.product.models import Product, ProductVariant

class Cart(models.Model):
    """购物车"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='用户')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'cart'
        verbose_name = '购物车'
        verbose_name_plural = '购物车'
    
    def __str__(self):
        return f'{self.user.username}的购物车'
    
    @property
    def total_items(self):
        """购物车商品总数量"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        """购物车总价格"""
        return sum(item.subtotal for item in self.items.all())
    
    def clear(self):
        """清空购物车"""
        try:
            if hasattr(self, 'items'):
                self.items.all().delete()
        except Exception as e:
            print(f"清空购物车时出错: {e}")
            raise

class CartItem(models.Model):
    """购物车商品项"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name='购物车')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, verbose_name='商品规格', null=True, blank=True)
    # 添加直接关联到产品的字段，以适应现有数据库结构
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='商品', null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, verbose_name='数量')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'cart_item'
        verbose_name = '购物车商品项'
        verbose_name_plural = '购物车商品项'
        unique_together = ['cart', 'product_variant']
    
    def __str__(self):
        if self.product_variant and hasattr(self.product_variant, 'product'):
            product_name = self.product_variant.product.name
            variant_info = f" - {self.product_variant.name}" if hasattr(self.product_variant, 'name') else ""
        elif self.product:
            product_name = self.product.name
            variant_info = ""
        else:
            product_name = 'Unknown Product'
            variant_info = ""
        return f'{product_name}{variant_info} x {self.quantity}'
    
    @property
    def get_product(self):
        """获取关联的产品"""
        if self.product_variant:
            return self.product_variant.product
        return self.product
    
    @property
    def unit_price(self):
        """单价"""
        try:
            if self.product_variant:
                return self.product_variant.price
            elif self.product:
                # 如果没有变体，使用产品的基础价格
                return self.product.base_price
            return 0
        except Exception as e:
            print(f"获取购物车项单价时出错: {e}")
            return 0
    
    @property
    def subtotal(self):
        """小计"""
        return self.unit_price * self.quantity
    
    def save(self, *args, **kwargs):
        # 确保数量不超过库存
        try:
            if self.product_variant:
                max_quantity = self.product_variant.stock
            elif self.product:
                # 如果没有指定变体，尝试获取产品的第一个变体的库存
                variant = self.product.variants.filter(is_active=True).first()
                max_quantity = variant.stock if variant else 999
            else:
                max_quantity = 999
            
            if self.quantity > max_quantity:
                self.quantity = max_quantity
        except Exception as e:
            print(f"保存购物车项时出错: {e}")
            # 如果出错，设置默认数量为1
            self.quantity = 1
        
        super().save(*args, **kwargs)