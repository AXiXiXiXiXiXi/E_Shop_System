from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import F, Sum, Model
from django.db import models as django_models
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer, AddCartItemSerializer, UpdateCartItemSerializer, RemoveCartItemSerializer
from apps.product.models import Product, ProductVariant
from django.db import transaction
from typing import Dict, Any, Optional, Union, Type, cast  # 添加更多类型导入
from rest_framework.serializers import Serializer
from django.db.transaction import atomic  # 导入atomic而不是直接使用transaction.atomic
import typing
from django.db import connection

# 添加类型定义，帮助类型检查器
class ValidatedData(Dict[str, Any]):
    def get(self, key: str, default=None) -> Any:
        return super().get(key, default)

# 自定义序列化器类型
class DRFSerializer:
    def is_valid(self, raise_exception=False) -> bool:
        return True
    
    @property
    def validated_data(self) -> ValidatedData:
        return ValidatedData()
    
    @property
    def data(self) -> Dict:
        return {}
    
    @property
    def errors(self) -> Dict:
        return {}

class CartViewSet(viewsets.ModelViewSet):
    """购物车视图集"""
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).prefetch_related('items__product_variant__product')
    
    def get_object(self):
        """获取当前用户的购物车"""
        try:
            with connection.cursor() as cursor:
                # 查询用户的购物车
                cursor.execute(
                    """
                    SELECT id FROM cart WHERE user_id = %s
                    """,
                    [self.request.user.id]
                )
                result = cursor.fetchone()
                
                if result:
                    cart_id = result[0]
                    # 返回一个简单的字典对象，只包含ID
                    return {'id': cart_id}
                else:
                    # 如果购物车不存在，创建一个
                    cursor.execute(
                        """
                        INSERT INTO cart (user_id, created_at, updated_at)
                        VALUES (%s, NOW(), NOW())
                        """,
                        [self.request.user.id]
                    )
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    cart_id = cursor.fetchone()[0]
                    return {'id': cart_id}
        except Exception as e:
            raise Exception(f"获取购物车失败: {str(e)}")
    
    def list(self, request, *args, **kwargs):
        """获取购物车列表"""
        try:
            # 获取用户的购物车
            with connection.cursor() as cursor:
                # 查询用户的购物车
                cursor.execute(
                    """
                    SELECT id FROM cart WHERE user_id = %s
                    """,
                    [request.user.id]
                )
                cart_result = cursor.fetchone()
                
                if not cart_result:
                    # 如果购物车不存在，创建一个
                    cursor.execute(
                        """
                        INSERT INTO cart (user_id, created_at, updated_at)
                        VALUES (%s, NOW(), NOW())
                        """,
                        [request.user.id]
                    )
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    cart_id = cursor.fetchone()[0]
                else:
                    cart_id = cart_result[0]
                
                # 先检查购物车项是否存在
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM cart_item WHERE cart_id = %s
                    """,
                    [cart_id]
                )
                count_result = cursor.fetchone()[0]
                
                if count_result == 0:
                    # 如果购物车为空，直接返回空数据
                    return Response({
                        'id': cart_id,
                        'items': [],
                        'total_price': 0,
                        'items_count': 0
                    })
                
                # 简化SQL查询，确保稳健性
                cursor.execute(
                    """
                    SELECT 
                        ci.id, ci.quantity, ci.created_at, ci.updated_at,
                        p.id as product_id, p.name, p.image, p.brand,
                        p.base_price as unit_price
                    FROM cart_item ci
                    JOIN product_product p ON ci.product_id = p.id
                    WHERE ci.cart_id = %s
                    """,
                    [cart_id]
                )
                
                cart_items = []
                for row in cursor.fetchall():
                    # 构建商品信息
                    product_info = {
                        'id': row[4],
                        'name': row[5],
                        'image': row[6],
                        'brand': row[7]
                    }
                    
                    # 尝试获取变体信息（如果存在）
                    variant_info = None
                    try:
                        # 获取商品的第一个可用变体
                        cursor.execute(
                            """
                            SELECT id, name, sku, price 
                            FROM product_productvariant 
                            WHERE product_id = %s AND is_active = 1
                            LIMIT 1
                            """,
                            [row[4]]
                        )
                        variant_result = cursor.fetchone()
                        
                        if variant_result:
                            variant_info = {
                                'id': variant_result[0],
                                'name': variant_result[1],
                                'sku': variant_result[2]
                            }
                            # 使用变体价格
                            unit_price = float(variant_result[3])
                        else:
                            # 使用产品基础价格
                            unit_price = float(row[8])
                    except Exception as e:
                        print(f"获取变体信息失败: {e}")
                        unit_price = float(row[8])
                    
                    # 构建完整的购物车项
                    cart_items.append({
                        'id': row[0],
                        'quantity': row[1],
                        'created_at': row[2],
                        'updated_at': row[3],
                        'product_info': product_info,
                        'variant_info': variant_info,
                        'unit_price': unit_price,
                        'subtotal': unit_price * row[1],
                        'product_image': row[6]  # 使用商品图片
                    })
                
                # 计算总价
                total_price = sum(item['subtotal'] for item in cart_items)
                
                # 构建响应数据
                cart_data = {
                    'id': cart_id,
                    'items': cart_items,
                    'total_price': total_price,
                    'items_count': len(cart_items)
                }
                
                return Response(cart_data)
                
        except Exception as e:
            print(f"购物车获取失败: {str(e)}")
            # 返回一个空购物车，避免前端崩溃
            return Response({
                'id': 0,
                'items': [],
                'total_price': 0,
                'items_count': 0,
                'error': f'获取购物车失败，请刷新重试: {str(e)}'
            })
    
    def create(self, request, *args, **kwargs):
        """创建购物车（实际上是获取现有购物车）"""
        return self.list(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        """获取购物车详情"""
        return self.list(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """更新购物车（不支持）"""
        return Response(
            {'error': '不支持直接更新购物车，请使用具体的操作接口'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def destroy(self, request, *args, **kwargs):
        """清空购物车"""
        try:
            cart = self.get_object()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM cart_item WHERE cart_id = %s
                    """,
                    [cart['id']]
                )
            return Response({'message': '购物车已清空'})
        except Exception as e:
            return Response(
                {'error': f'清空购物车失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """清空购物车 - 自定义action"""
        try:
            cart = self.get_object()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM cart_item WHERE cart_id = %s
                    """,
                    [cart['id']]
                )
            return Response({'message': '购物车已清空'})
        except Exception as e:
            return Response(
                {'error': f'清空购物车失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """添加商品到购物车 - 使用原始SQL"""
        serializer = AddCartItemSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
            
            try:
                # 获取购物车
                with connection.cursor() as cursor:
                    # 查询用户的购物车
                    cursor.execute(
                        """
                        SELECT id FROM cart WHERE user_id = %s
                        """,
                        [request.user.id]
                    )
                    cart_result = cursor.fetchone()
                    
                    if not cart_result:
                        # 如果购物车不存在，创建一个
                        cursor.execute(
                            """
                            INSERT INTO cart (user_id, created_at, updated_at)
                            VALUES (%s, NOW(), NOW())
                            """,
                            [request.user.id]
                        )
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        cart_id = cursor.fetchone()[0]
                    else:
                        cart_id = cart_result[0]
                
                    # 检查商品是否存在
                    cursor.execute(
                        "SELECT id, status FROM product_product WHERE id = %s",
                        [product_id]
                    )
                    product_result = cursor.fetchone()
                    
                    if not product_result or product_result[1] != 'active':
                        return Response({
                            'error': '商品不存在或已下架'
                        }, status=status.HTTP_404_NOT_FOUND)
                    
                    # 检查购物车中是否已有此商品
                    cursor.execute(
                        "SELECT id, quantity FROM cart_item WHERE cart_id = %s AND product_id = %s",
                        [cart_id, product_id]
                    )
                    cart_item_result = cursor.fetchone()
                    
                    if cart_item_result:
                        # 如果购物车中已有此商品，更新数量
                        item_id, current_quantity = cart_item_result
                        new_quantity = current_quantity + quantity
                        
                        cursor.execute(
                            "UPDATE cart_item SET quantity = %s, updated_at = NOW() WHERE id = %s",
                            [new_quantity, item_id]
                        )
                        
                        # 获取更新后的商品基本信息
                        cursor.execute(
                            """
                            SELECT p.id, p.name, p.image, p.brand, p.base_price
                            FROM product_product p
                            WHERE p.id = %s
                            """,
                            [product_id]
                        )
                        product_data = cursor.fetchone()
                        
                        if product_data:
                            # 获取变体信息（如果有）
                            cursor.execute(
                                """
                                SELECT id, name, sku, price 
                                FROM product_productvariant 
                                WHERE product_id = %s AND is_active = 1
                                LIMIT 1
                                """,
                                [product_id]
                            )
                            variant_result = cursor.fetchone()
                            
                            variant_info = None
                            if variant_result:
                                variant_info = {
                                    'id': variant_result[0],
                                    'name': variant_result[1],
                                    'sku': variant_result[2]
                                }
                                unit_price = float(variant_result[3])
                            else:
                                unit_price = float(product_data[4])
                            
                            product_info = {
                                'id': product_data[0],
                                'name': product_data[1],
                                'image': product_data[2],
                                'brand': product_data[3]
                            }
                            
                            cart_item_data = {
                                'id': item_id,
                                'quantity': new_quantity,
                                'product_info': product_info,
                                'variant_info': variant_info,
                                'unit_price': unit_price,
                                'subtotal': unit_price * new_quantity,
                                'product_image': product_data[2]
                            }
                            
                            return Response({
                                'message': '商品已添加到购物车',
                                'cart_item': cart_item_data
                            }, status=status.HTTP_200_OK)
                    else:
                        # 如果购物车中没有此商品，创建新项
                        cursor.execute(
                            """
                            INSERT INTO cart_item (cart_id, product_id, quantity, created_at, updated_at)
                            VALUES (%s, %s, %s, NOW(), NOW())
                            """,
                            [cart_id, product_id, quantity]
                        )
                        
                        # 获取新插入的ID
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        item_id = cursor.fetchone()[0]
                        
                        # 获取商品基本信息
                        cursor.execute(
                            """
                            SELECT p.id, p.name, p.image, p.brand, p.base_price
                            FROM product_product p
                            WHERE p.id = %s
                            """,
                            [product_id]
                        )
                        product_data = cursor.fetchone()
                        
                        if product_data:
                            # 获取变体信息（如果有）
                            cursor.execute(
                                """
                                SELECT id, name, sku, price 
                                FROM product_productvariant 
                                WHERE product_id = %s AND is_active = 1
                                LIMIT 1
                                """,
                                [product_id]
                            )
                            variant_result = cursor.fetchone()
                            
                            variant_info = None
                            if variant_result:
                                variant_info = {
                                    'id': variant_result[0],
                                    'name': variant_result[1],
                                    'sku': variant_result[2]
                                }
                                unit_price = float(variant_result[3])
                            else:
                                unit_price = float(product_data[4])
                            
                            product_info = {
                                'id': product_data[0],
                                'name': product_data[1],
                                'image': product_data[2],
                                'brand': product_data[3]
                            }
                            
                            cart_item_data = {
                                'id': item_id,
                                'quantity': quantity,
                                'product_info': product_info,
                                'variant_info': variant_info,
                                'unit_price': unit_price,
                                'subtotal': unit_price * quantity,
                                'product_image': product_data[2]
                            }
                            
                            return Response({
                                'message': '商品已添加到购物车',
                                'cart_item': cart_item_data
                            }, status=status.HTTP_201_CREATED)
                        
                return Response({
                    'error': '添加商品到购物车失败，请重试'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            except Exception as e:
                print(f"添加商品到购物车失败: {str(e)}")
                return Response({
                    'error': f'添加商品到购物车失败: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def update_item(self, request):
        """更新购物车项数量"""
        serializer = UpdateCartItemSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            cart_item_id = data.get('cart_item_id')
            quantity = data.get('quantity')
            
            if quantity < 1:
                return Response({
                    'error': '数量必须大于0'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                with connection.cursor() as cursor:
                    # 查询购物车项是否属于当前用户
                    cursor.execute(
                        """
                        SELECT ci.id, ci.product_id, p.base_price
                        FROM cart_item ci
                        JOIN cart c ON ci.cart_id = c.id
                        JOIN product_product p ON ci.product_id = p.id
                        WHERE ci.id = %s AND c.user_id = %s
                        """,
                        [cart_item_id, request.user.id]
                    )
                    item_result = cursor.fetchone()
                    
                    if not item_result:
                        return Response({
                            'error': '购物车项不存在或不属于当前用户'
                        }, status=status.HTTP_404_NOT_FOUND)
                    
                    # 更新购物车项数量
                    cursor.execute(
                        """
                        UPDATE cart_item SET quantity = %s, updated_at = NOW()
                        WHERE id = %s
                        """,
                        [quantity, cart_item_id]
                    )
                    
                    # 获取商品基本信息
                    product_id = item_result[1]
                    cursor.execute(
                        """
                        SELECT p.id, p.name, p.image, p.brand, p.base_price
                        FROM product_product p
                        WHERE p.id = %s
                        """,
                        [product_id]
                    )
                    product_data = cursor.fetchone()
                    
                    if product_data:
                        # 获取变体信息（如果有）
                        cursor.execute(
                            """
                            SELECT id, name, sku, price 
                            FROM product_productvariant 
                            WHERE product_id = %s AND is_active = 1
                            LIMIT 1
                            """,
                            [product_id]
                        )
                        variant_result = cursor.fetchone()
                        
                        variant_info = None
                        if variant_result:
                            variant_info = {
                                'id': variant_result[0],
                                'name': variant_result[1],
                                'sku': variant_result[2]
                            }
                            unit_price = float(variant_result[3])
                        else:
                            unit_price = float(product_data[4])
                        
                        product_info = {
                            'id': product_data[0],
                            'name': product_data[1],
                            'image': product_data[2],
                            'brand': product_data[3]
                        }
                        
                        cart_item_data = {
                            'id': cart_item_id,
                            'quantity': quantity,
                            'product_info': product_info,
                            'variant_info': variant_info,
                            'unit_price': unit_price,
                            'subtotal': unit_price * quantity,
                            'product_image': product_data[2]
                        }
                        
                        return Response({
                            'message': '购物车数量已更新',
                            'cart_item': cart_item_data
                        })
                    
                    return Response({
                        'message': '购物车数量已更新'
                    })
                    
            except Exception as e:
                print(f"更新购物车数量失败: {str(e)}")
                return Response({
                    'error': f'更新购物车数量失败: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """从购物车中移除商品"""
        serializer = RemoveCartItemSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            cart_item_id = data.get('cart_item_id')
            
            try:
                with connection.cursor() as cursor:
                    # 查询购物车项是否属于当前用户
                    cursor.execute(
                        """
                        SELECT ci.id
                        FROM cart_item ci
                        JOIN cart c ON ci.cart_id = c.id
                        WHERE ci.id = %s AND c.user_id = %s
                        """,
                        [cart_item_id, request.user.id]
                    )
                    item_result = cursor.fetchone()
                    
                    if not item_result:
                        return Response({
                            'error': '购物车项不存在或不属于当前用户'
                        }, status=status.HTTP_404_NOT_FOUND)
                    
                    # 删除购物车项
                    cursor.execute(
                        """
                        DELETE FROM cart_item WHERE id = %s
                        """,
                        [cart_item_id]
                    )
                    
                    return Response({
                        'message': '商品已从购物车中移除'
                    })
                    
            except Exception as e:
                print(f"从购物车移除商品失败: {str(e)}")
                return Response({
                    'error': f'从购物车移除商品失败: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """获取购物车摘要信息（总价、商品数量等）"""
        try:
            cart = self.get_object()
            
            with connection.cursor() as cursor:
                # 获取购物车项总数和总数量
                cursor.execute(
                    """
                    SELECT COUNT(id) as items_count, SUM(quantity) as total_quantity
                    FROM cart_item
                    WHERE cart_id = %s
                    """,
                    [cart['id']]
                )
                result = cursor.fetchone()
                items_count = result[0] or 0
                total_quantity = result[1] or 0
                
                # 计算总价，使用变体价格
                cursor.execute(
                    """
                    SELECT 
                        SUM(
                            ci.quantity * COALESCE(
                                (SELECT MIN(pv.price) FROM product_productvariant pv WHERE pv.product_id = p.id),
                                p.base_price,
                                0
                            )
                        ) as total_price
                    FROM cart_item ci
                    JOIN product_product p ON ci.product_id = p.id
                    WHERE ci.cart_id = %s
                    """,
                    [cart['id']]
                )
                result = cursor.fetchone()
                total_price = float(result[0]) if result[0] else 0
                
                return Response({
                    'items_count': items_count,  # 不同商品种类数量
                    'total_quantity': total_quantity,  # 商品总数量
                    'total_price': total_price,  # 商品总价
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'error': f'获取购物车摘要失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CartItemViewSet(viewsets.ReadOnlyModelViewSet):
    """购物车商品项视图集 - 只读"""
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # 忽略Django ORM类型检查错误
        return CartItem.objects.filter(  # type: ignore
            cart__user=self.request.user
        ).select_related('product_variant__product')