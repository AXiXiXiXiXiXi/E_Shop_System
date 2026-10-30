from rest_framework import serializers
from .models import Cart, CartItem
from apps.product.models import Product, ProductVariant
from apps.product.serializers import ProductVariantSerializer

class CartItemSerializer(serializers.ModelSerializer):
    """购物车项序列化器"""
    product_info = serializers.SerializerMethodField()
    variant_info = serializers.SerializerMethodField()
    unit_price = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product_info', 'variant_info', 'quantity', 'unit_price', 'subtotal', 'created_at', 'updated_at']
    
    def get_product_info(self, obj):
        # 使用原始SQL获取产品信息
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.id, p.name, p.image, p.brand
                FROM product_product p
                JOIN cart_item ci ON p.id = ci.product_id
                WHERE ci.id = %s
                """,
                [obj.id]
            )
            result = cursor.fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'image': result[2],
                    'brand': result[3]
                }
        return None
    
    def get_variant_info(self, obj):
        # 尝试获取产品的第一个变体作为默认变体
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pv.id, pv.name, pv.sku, pv.price, pv.original_price, pv.stock
                FROM product_productvariant pv
                JOIN cart_item ci ON pv.product_id = ci.product_id
                WHERE ci.id = %s
                LIMIT 1
                """,
                [obj.id]
            )
            result = cursor.fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'sku': result[2],
                    'price': float(result[3]),
                    'original_price': float(result[4]) if result[4] else None,
                    'stock': result[5]
                }
        return None
    
    def get_unit_price(self, obj):
        # 获取单价
        from django.db import connection
        
        with connection.cursor() as cursor:
            # 尝试从变体获取价格
            cursor.execute(
                """
                SELECT pv.price
                FROM product_productvariant pv
                JOIN cart_item ci ON pv.product_id = ci.product_id
                WHERE ci.id = %s
                LIMIT 1
                """,
                [obj.id]
            )
            result = cursor.fetchone()
            
            if result:
                return float(result[0])
            
            # 如果没有变体，尝试从产品获取基础价格
            cursor.execute(
                """
                SELECT p.base_price
                FROM product_product p
                JOIN cart_item ci ON p.id = ci.product_id
                WHERE ci.id = %s
                """,
                [obj.id]
            )
            result = cursor.fetchone()
            
            if result:
                return float(result[0])
        
        return 0
    
    def get_subtotal(self, obj):
        # 计算小计
        return self.get_unit_price(obj) * obj.quantity

class CartSerializer(serializers.ModelSerializer):
    """购物车序列化器"""
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price', 'items_count', 'created_at', 'updated_at']
    
    def get_total_price(self, obj):
        return sum(item.subtotal for item in obj.items.all()) if obj.items.exists() else 0
    
    def get_items_count(self, obj):
        return obj.items.count()

class AddCartItemSerializer(serializers.Serializer):
    """添加商品到购物车序列化器"""
    product_id = serializers.IntegerField(required=True)
    variant_id = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(min_value=1, required=True)
    
    def validate(self, data):
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        
        # 检查产品是否存在
        try:
            product = Product.objects.get(id=product_id, status='active')
        except Product.DoesNotExist:
            raise serializers.ValidationError("商品不存在或已下架")
        
        # 如果提供了变体ID，检查变体是否存在
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("商品规格不存在或已下架")
        
        # 如果没有提供变体ID，尝试获取默认变体
        else:
            variants = ProductVariant.objects.filter(product=product, is_active=True)
            if not variants.exists():
                raise serializers.ValidationError("该商品没有可用规格")
            
            # 使用第一个变体作为默认
            variant = variants.first()
            data['variant_id'] = variant.id
        
        return data

class UpdateCartItemSerializer(serializers.Serializer):
    """更新购物车商品项序列化器"""
    cart_item_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        cart_item = self.instance
        if cart_item and hasattr(cart_item, 'product_variant'):
            max_quantity = cart_item.product_variant.stock
            if value > max_quantity:
                raise serializers.ValidationError(f'库存不足，最多可购买{max_quantity}件')
        return value

class RemoveCartItemSerializer(serializers.Serializer):
    """从购物车移除商品的序列化器"""
    cart_item_id = serializers.IntegerField()