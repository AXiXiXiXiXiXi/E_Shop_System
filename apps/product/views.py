import logging
from django.db.models import Q, F, Count, Min, Max, Avg
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from .models import Category, Product, ProductVariant
from .serializers import (
    CategorySerializer, CategoryTreeSerializer,
    ProductListSerializer, ProductDetailSerializer, ProductVariantSerializer
)

# 获取logger
logger = logging.getLogger(__name__)

class ProductPagination(PageNumberPagination):
    """商品分页器"""
    page_size = 12  # 每页显示12个商品卡片
    page_size_query_param = 'page_size'
    max_page_size = 100

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """商品分类视图集"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'tree':
            return CategoryTreeSerializer
        return CategorySerializer
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取分类树形结构"""
        # 只获取顶级分类
        queryset = Category.objects.filter(parent__isnull=True, is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """商品视图集"""
    queryset = Product.objects.filter(status='active')
    serializer_class = ProductListSerializer
    pagination_class = ProductPagination
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]  # 移除OrderingFilter，避免与自定义排序冲突
    search_fields = ['name', 'description', 'brand']
    # 移除ordering和ordering_fields，使用自定义排序逻辑
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 记录请求参数
        logger.info(f"请求参数: {self.request.query_params}")
        
        # 按分类筛选
        category_id = self.request.query_params.get('category')
        if category_id:
            # 获取该分类及其所有子分类
            categories = []
            try:
                main_category = Category.objects.get(id=category_id)
                categories.append(main_category.id)
                
                # 添加子分类
                children = Category.objects.filter(parent=main_category)
                categories.extend(children.values_list('id', flat=True))
                
                queryset = queryset.filter(category_id__in=categories)
            except Category.DoesNotExist:
                pass
        
        # 按品牌筛选
        brand = self.request.query_params.get('brand')
        if brand:
            queryset = queryset.filter(brand=brand)
        
        # 按价格范围筛选
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price or max_price:
            variants = ProductVariant.objects.all()
            
            if min_price:
                variants = variants.filter(price__gte=min_price)
            
            if max_price:
                variants = variants.filter(price__lte=max_price)
            
            product_ids = variants.values_list('product_id', flat=True).distinct()
            queryset = queryset.filter(id__in=product_ids)
        
        # 是否只查询推荐商品
        featured = self.request.query_params.get('featured')
        if featured and featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # 处理排序参数
        sort = self.request.query_params.get('sort')
        if sort:
            logger.info(f"排序参数: {sort}")
            
            # 记录排序前的产品ID顺序
            pre_sort_ids = list(queryset.values_list('id', flat=True))
            logger.info(f"排序前的产品ID: {pre_sort_ids}")
            
            if sort == 'price_asc':
                # 使用商品变体的最低价格排序
                from django.db.models import Min
                queryset = queryset.annotate(
                    min_variant_price=Min('variants__price')
                ).order_by('min_variant_price')
                logger.info("按变体最低价格升序排序")
            elif sort == 'price_desc':
                # 使用商品变体的最低价格排序
                from django.db.models import Min
                queryset = queryset.annotate(
                    min_variant_price=Min('variants__price')
                ).order_by('-min_variant_price')
                logger.info("按变体最低价格降序排序")
            elif sort == 'rating':
                queryset = queryset.order_by('-rating')
                logger.info("按评分排序")
            elif sort == 'newest':
                queryset = queryset.order_by('-created_at')
                logger.info("按最新上架排序")
            elif sort == 'bestselling':
                queryset = queryset.order_by('-sales_count')
                logger.info("按销量排序")
                
            # 记录排序后的产品ID顺序
            post_sort_ids = list(queryset.values_list('id', flat=True))
            logger.info(f"排序后的产品ID: {post_sort_ids}")
        
        # 记录SQL查询语句
        logger.info(f"SQL查询: {queryset.query}")
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 增加浏览次数
        Product.objects.filter(id=instance.id).update(view_count=F('view_count') + 1)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get', 'head'], url_path='(?P<product_id>\\d+)/exists', permission_classes=[])
    def exists(self, request, product_id=None):
        """检查商品ID是否存在，如果是变体ID则返回对应的主产品ID"""
        if not product_id:
            return Response({"error": "必须提供商品ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product_id_int = int(product_id)
            print(f"\n==== 检查商品ID {product_id_int} 是否存在 ====")
            
            from .models import Product, ProductVariant
            
            # 首先检查是否为主产品ID
            try:
                product = Product.objects.get(id=product_id_int)
                print(f"找到主产品: ID={product.id}, 名称={product.name}")
                return Response({
                    "exists": True,
                    "is_main_product": True,
                    "product_id": product.id,
                    "product_name": product.name,
                    "original_id": product_id_int
                })
                
            except Product.DoesNotExist:
                print(f"ID {product_id_int} 不是主产品ID，检查是否为变体ID...")
                
                try:
                    # 检查是否为变体ID
                    variant = ProductVariant.objects.get(id=product_id_int)
                    
                    # 获取对应的主产品
                    try:
                        product = Product.objects.get(id=variant.product_id)
                        print(f"通过变体ID {product_id_int} 找到主产品: ID={product.id}, 名称={product.name}")
                        return Response({
                            "exists": True,
                            "is_main_product": False,
                            "is_variant": True,
                            "variant_id": variant.id,
                            "variant_name": variant.name,
                            "product_id": product.id,  # 真实的主产品ID
                            "product_name": product.name,
                            "original_id": product_id_int,
                            "mapping_message": f"变体ID {product_id_int} 映射到主产品ID {product.id}"
                        })
                        
                    except Product.DoesNotExist:
                        print(f"错误: 变体指向的主产品ID {variant.product_id} 不存在")
                        return Response({
                            "exists": False,
                            "error": "变体对应的主产品不存在",
                            "variant_id": variant.id,
                            "original_id": product_id_int
                        }, status=status.HTTP_404_NOT_FOUND)
                        
                except ProductVariant.DoesNotExist:
                    print(f"ID {product_id_int} 既不是主产品ID也不是变体ID")
                    return Response({
                        "exists": False,
                        "error": f"商品ID {product_id_int} 不存在",
                        "original_id": product_id_int,
                        "id_not_found": True
                    }, status=status.HTTP_404_NOT_FOUND)
                    
        except ValueError:
            print(f"无效的商品ID: {product_id}")
            return Response({
                "exists": False,
                "error": "商品ID必须为整数"
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """搜索商品"""
        keyword = request.query_params.get('keyword', '')
        if not keyword:
            return Response({'message': '请输入搜索关键词'}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset().filter(
            Q(name__icontains=keyword) | 
            Q(description__icontains=keyword) | 
            Q(brand__icontains=keyword)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """获取推荐商品"""
        queryset = self.get_queryset().filter(is_featured=True)[:8]
        serializer = ProductListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """获取最新商品"""
        queryset = self.get_queryset().order_by('-created_at')[:8]
        serializer = ProductListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def bestselling(self, request):
        """获取畅销商品"""
        queryset = self.get_queryset().order_by('-sales_count')[:8]
        serializer = ProductListSerializer(queryset, many=True)
        return Response(serializer.data)

class ProductVariantViewSet(viewsets.ReadOnlyModelViewSet):
    """商品变体视图集"""
    queryset = ProductVariant.objects.filter(is_active=True)
    serializer_class = ProductVariantSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset 