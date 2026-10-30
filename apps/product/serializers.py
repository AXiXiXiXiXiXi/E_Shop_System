from rest_framework import serializers
from .models import Category, Product, ProductVariant

class CategorySerializer(serializers.ModelSerializer):
    """商品分类序列化器"""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent', 'sort_order', 'is_active']

class CategoryTreeSerializer(serializers.ModelSerializer):
    """商品分类树形序列化器"""
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'children', 'sort_order', 'is_active']
    
    def get_children(self, obj):
        """获取子分类"""
        children = Category.objects.filter(parent=obj, is_active=True)
        serializer = CategoryTreeSerializer(children, many=True)
        return serializer.data

class ProductVariantSerializer(serializers.ModelSerializer):
    """商品变体序列化器"""
    is_on_sale = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'sku', 'price', 'original_price', 
            'stock', 'is_active', 'attributes', 'weight',
            'is_on_sale', 'discount_percentage'
        ]

class ProductListSerializer(serializers.ModelSerializer):
    """商品列表序列化器"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    price_min = serializers.DecimalField(source='price_range.min', max_digits=10, decimal_places=2, read_only=True)
    price_max = serializers.DecimalField(source='price_range.max', max_digits=10, decimal_places=2, read_only=True)
    default_variant_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'image', 'category', 'category_name',
            'price_min', 'price_max', 'base_price', 'brand', 'status',
            'is_featured', 'rating', 'sales_count', 'default_variant_id',
            'created_at'
        ]
    
    def get_default_variant_id(self, obj):
        """获取默认变体ID"""
        default_variant = obj.variants.filter(is_active=True).first()
        return default_variant.id if default_variant else None

class ProductDetailSerializer(serializers.ModelSerializer):
    """商品详情序列化器"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'brand', 'image', 'images', 'status', 'is_featured',
            'rating', 'sales_count', 'view_count', 'variants',
            'created_at', 'updated_at'
        ] 