from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Review, AfterSaleRequest, AfterSaleChatMessage
from .serializers import ReviewSerializer, AfterSaleRequestSerializer, AfterSaleChatMessageSerializer
from apps.order.models import OrderItem

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """创建新评价"""
        user = request.user
        data = request.data.copy()
        
        print(f"\n==== 用户 {user.username} 创建评价 ====")
        print(f"接收到的数据: {data}")
        
        # 获取商品ID，可能是Product ID或ProductVariant ID
        raw_product_id = data.get('product_id')
        
        if not raw_product_id:
            print("错误: 缺少商品ID")
            return Response({"error": "必须提供商品ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            raw_product_id = int(raw_product_id)
            print(f"原始商品ID: {raw_product_id}")
            
            # 确定真实的主产品ID
            from apps.product.models import Product, ProductVariant
            
            # 首先检查是否为主产品ID
            real_product_id = None
            product_name = None
            
            try:
                # 尝试作为主产品ID查找
                product = Product.objects.get(id=raw_product_id)
                real_product_id = product.id
                product_name = product.name
                print(f"直接找到主产品: ID={real_product_id}, 名称={product_name}")
                
            except Product.DoesNotExist:
                print(f"ID {raw_product_id} 不是主产品ID，尝试作为变体ID查找...")
                
                try:
                    # 尝试作为变体ID查找
                    variant = ProductVariant.objects.get(id=raw_product_id)
                    real_product_id = variant.product_id  # 获取对应的主产品ID
                    
                    # 获取主产品信息
                    try:
                        product = Product.objects.get(id=real_product_id)
                        product_name = product.name
                        print(f"通过变体ID {raw_product_id} 找到主产品: ID={real_product_id}, 名称={product_name}")
                        
                    except Product.DoesNotExist:
                        print(f"错误: 变体指向的主产品ID {real_product_id} 不存在")
                        return Response({
                            "error": f"变体对应的主产品不存在"
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                except ProductVariant.DoesNotExist:
                    print(f"错误: ID {raw_product_id} 既不是主产品ID也不是变体ID")
                    return Response({
                        "error": f"商品ID {raw_product_id} 不存在"
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # 强制使用主产品ID和名称
            data['product_id'] = real_product_id
            data['product_name'] = product_name
            print(f"最终使用的产品信息: ID={real_product_id}, 名称={product_name}")
            
            # 检查用户是否已经评价过该主产品
            existing_review = Review.objects.filter(user=user, product_id=real_product_id).first()
            if existing_review:
                print(f"用户已评价过该产品 ID {real_product_id}")
                return Response({"error": "您已经评价过该商品"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 创建评价 - 不需要手动设置user，perform_create会处理
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                review = serializer.save(user=user)  # 直接传递user参数
                print(f"评价创建成功: 评价ID={review.id}, 产品ID={review.product_id}, 产品名称={review.product_name}")
                
                # 验证保存的数据
                saved_review = Review.objects.get(id=review.id)
                print(f"验证保存的评价: ID={saved_review.id}, 产品ID={saved_review.product_id}, 产品名称={saved_review.product_name}, 用户={saved_review.user.username}")
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                print(f"序列化验证失败: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except ValueError:
            print(f"错误: 商品ID必须为整数，收到: {raw_product_id}")
            return Response({"error": "商品ID必须为整数"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"创建评价时发生未知错误: {str(e)}")
            return Response({"error": "创建评价失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
        """更新评价 - 确保用户只能修改自己的评论"""
        user = request.user
        
        try:
            # 获取要更新的评论
            review = self.get_object()
            
            print(f"\n==== 用户 {user.username} 更新评论ID {pk} ====")
            print(f"评论原始数据: 用户={review.user.username}, 商品={review.product_name}, 评分={review.rating}")
            print(f"接收到的更新数据: {request.data}")
            
            # 检查权限：用户只能修改自己的评论
            if review.user != user:
                print(f"权限错误: 用户 {user.username} 尝试修改用户 {review.user.username} 的评论")
                return Response({"error": "您只能修改自己的评论"}, status=status.HTTP_403_FORBIDDEN)
            
            # 更新评论数据
            data = request.data.copy()
            
            # 更新序列化器
            serializer = self.get_serializer(review, data=data, partial=True)
            if serializer.is_valid():
                updated_review = serializer.save()
                print(f"评论更新成功: ID={updated_review.id}, 新评分={updated_review.rating}")
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                print(f"序列化验证失败: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Review.DoesNotExist:
            print(f"评论ID {pk} 不存在")
            return Response({"error": "评论不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"更新评论时发生错误: {str(e)}")
            return Response({"error": "更新评论失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='user-reviews')
    def user_reviews(self, request):
        """获取当前用户的所有评价"""
        reviews = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='user-product/(?P<product_id>\\d+)')
    def user_product_review(self, request, product_id=None):
        """获取当前用户对指定商品的评价"""
        user = request.user
        print(f"\n==== 获取用户 {user.username} 对商品ID {product_id} 的评价 ====")
        
        if not product_id:
            print(f"错误: 未提供商品ID")
            return Response({"error": "必须提供商品ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product_id_int = int(product_id)
            print(f"查询商品ID: {product_id_int} 的评价")
            
            # 首先尝试直接查找商品ID
            from apps.product.models import Product, ProductVariant
            product_exists = Product.objects.filter(id=product_id_int).exists()
            
            # 如果ID不是有效的商品ID，检查是否为变体ID
            real_product_id = product_id_int
            if not product_exists:
                print(f"商品ID {product_id_int} 不存在于产品表中，检查是否为变体ID...")
                
                try:
                    # 查询变体表，找到对应的商品ID
                    variant = ProductVariant.objects.filter(id=product_id_int).first()
                    if variant:
                        real_product_id = variant.product_id
                        print(f"找到对应变体的商品ID: {real_product_id}")
                        product_exists = True
                    else:
                        print(f"未找到ID为 {product_id_int} 的变体")
                        # 即使找不到对应的变体，也返回一个有效的响应，而不是404错误
                        response_data = {
                            "exists": False, 
                            "message": "未找到该商品或变体ID",
                            "original_id": product_id_int,
                            "real_product_id": product_id_int,  # 保持一致，表示未找到映射
                            "id_not_found": True  # 添加一个标志，表示ID完全不存在
                        }
                        return Response(response_data, status=status.HTTP_404_NOT_FOUND)
                except Exception as e:
                    print(f"查询变体时出错: {str(e)}")
                    # 即使出错，也返回一个有效的响应
                    return Response({
                        "exists": False,
                        "message": f"查询变体时出错: {str(e)}",
                        "original_id": product_id_int,
                        "error": True
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # 使用最终确定的商品ID查询评论
            review = self.queryset.filter(product_id=real_product_id, user=user).first()
            
            if review:
                print(f"找到评价 ID: {review.id}, 评分: {review.rating}, 商品ID: {review.product_id}")
                serializer = self.get_serializer(review)
                return Response(serializer.data)
            else:
                print(f"未找到商品 ID {real_product_id} 的评价")
                
                # 修改返回数据，明确告知前端真实的商品ID
                response_data = {
                    "exists": False, 
                    "message": "未找到该商品的评价",
                    "original_id": product_id_int,
                    "real_product_id": real_product_id
                }
                
                # 如果ID发生了映射，添加更明确的提示和商品名称
                if real_product_id != product_id_int:
                    # 获取真实商品的名称
                    try:
                        real_product = Product.objects.get(id=real_product_id)
                        product_name = real_product.name
                        print(f"获取到真实商品名称: {product_name}")
                    except Product.DoesNotExist:
                        product_name = f"商品ID{real_product_id}"
                        print(f"警告: 无法找到商品ID {real_product_id} 的名称")
                    
                    response_data["id_mapped"] = True
                    response_data["mapping_message"] = f"商品变体ID {product_id_int} 已映射到产品ID {real_product_id}"
                    response_data["product_name"] = product_name  # 添加正确的商品名称
                
                return Response(response_data, status=status.HTTP_404_NOT_FOUND)
                
        except ValueError:
            print(f"错误: 商品ID必须为整数，收到的值: {product_id}")
            return Response({"error": "商品ID必须为整数"}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='product/(?P<product_id>\\d+)', permission_classes=[])
    def product_reviews(self, request, product_id=None):
        """获取指定商品的所有评价"""
        if not product_id:
            return Response({"error": "必须提供商品ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"\n==== 获取商品 ID {product_id} 的评论 ====")
        
        # 确保product_id是整数
        try:
            product_id_int = int(product_id)
            
            # 首先尝试直接查找商品ID
            from apps.product.models import Product, ProductVariant
            product_exists = Product.objects.filter(id=product_id_int).exists()
            
            # 如果ID不是有效的商品ID，检查是否为变体ID
            real_product_id = product_id_int
            variant_ids = []  # 用于存储与该产品相关的所有变体ID
            
            # 如果是有效产品ID，查找该产品的所有变体ID
            if product_exists:
                try:
                    # 获取该产品的所有变体
                    variants = ProductVariant.objects.filter(product_id=product_id_int)
                    variant_ids = list(variants.values_list('id', flat=True))
                    print(f"产品ID {product_id_int} 的变体IDs: {variant_ids}")
                except Exception as e:
                    print(f"查询产品变体时出错: {str(e)}")
            else:
                # 如果不是有效产品ID，检查是否为变体ID
                print(f"商品ID {product_id_int} 不存在于产品表中，检查是否为变体ID...")
                
                try:
                    # 查询变体表，找到对应的商品ID
                    variant = ProductVariant.objects.filter(id=product_id_int).first()
                    if variant:
                        real_product_id = variant.product_id
                        print(f"找到对应变体的商品ID: {real_product_id}")
                        product_exists = True
                        
                        # 获取该产品的所有变体
                        variants = ProductVariant.objects.filter(product_id=real_product_id)
                        variant_ids = list(variants.values_list('id', flat=True))
                        print(f"通过变体ID {product_id_int} 找到产品ID {real_product_id} 的所有变体IDs: {variant_ids}")
                    else:
                        print(f"未找到ID为 {product_id_int} 的变体")
                        # 如果既不是产品ID也不是变体ID，返回明确的错误信息
                        return Response({
                            "error": f"ID {product_id_int} 既不是有效的产品ID，也不是有效的变体ID",
                            "total": 0,
                            "average_rating": 0,
                            "rating_counts": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
                            "reviews": [],
                            "id_not_found": True,
                            "original_id": product_id_int
                        }, status=status.HTTP_404_NOT_FOUND)
                except Exception as e:
                    print(f"查询变体时出错: {str(e)}")
                    # 返回错误信息
                    return Response({
                        "error": f"查询变体时出错: {str(e)}",
                        "total": 0,
                        "average_rating": 0,
                        "rating_counts": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
                        "reviews": [],
                        "api_error": True,
                        "original_id": product_id_int
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 使用最终确定的商品ID查询评论
            print(f"查询条件: 产品ID={real_product_id} 或 产品ID在变体IDs={variant_ids}")
            
            # 查询直接关联到该产品的评论，或者关联到该产品任何变体的评论
            from django.db.models import Q
            if variant_ids:
                # 使用Q对象构建OR条件: product_id = real_product_id OR product_id IN variant_ids
                reviews = self.queryset.filter(
                    Q(product_id=real_product_id) | Q(product_id__in=variant_ids)
                ).order_by('-created_at')
            else:
                # 只查询直接关联到产品ID的评论
                reviews = self.queryset.filter(product_id=real_product_id).order_by('-created_at')
                
            print(f"数据库中找到评论数量: {reviews.count()}")
            
            # 如果ID转换了，记录日志
            if real_product_id != product_id_int:
                print(f"注意: 原始ID {product_id_int} 已转换为商品ID {real_product_id} 进行查询")
            
            # 调试：检查查询到的评论对象
            for idx, review in enumerate(reviews):
                print(f"评论 #{idx+1} - ID: {review.id}")
                print(f"  用户: {review.user.username}")
                print(f"  商品ID: {review.product_id} (字符串比较: {str(review.product_id) == str(real_product_id)})")
                print(f"  商品名称: '{review.product_name}'")
                print(f"  评分: {review.rating}")
                print(f"  内容: '{review.content}'")
                print(f"  创建时间: {review.created_at}")
            
            serializer = self.get_serializer(reviews, many=True)
            
            # 调试：打印序列化后的数据
            serialized_data = serializer.data
            print(f"序列化后的评论数量: {len(serialized_data)}")
            for idx, review_data in enumerate(serialized_data):
                print(f"序列化评论 #{idx+1}:")
                print(f"  ID: {review_data.get('id')}")
                print(f"  用户ID: {review_data.get('user_id')}")
                print(f"  用户名: {review_data.get('username')}")
                print(f"  商品ID: {review_data.get('product_id')}")
                print(f"  评分: {review_data.get('rating')}")
                print(f"  内容: '{review_data.get('content')}'")
                if 'product_name' in review_data:
                    print(f"  商品名称: {review_data.get('product_name')}")
                print(f"  创建时间: {review_data.get('created_at')}")
            
            # 计算评分统计
            total_reviews = reviews.count()
            if total_reviews > 0:
                avg_rating = sum(review.rating for review in reviews) / total_reviews
                rating_counts = {
                    "5": reviews.filter(rating=5).count(),
                    "4": reviews.filter(rating=4).count(),
                    "3": reviews.filter(rating=3).count(),
                    "2": reviews.filter(rating=2).count(),
                    "1": reviews.filter(rating=1).count(),
                }
                
                result = {
                    "total": total_reviews,
                    "average_rating": round(avg_rating, 1),
                    "rating_counts": rating_counts,
                    "reviews": serialized_data,
                    "original_id": product_id_int,
                    "product_id": real_product_id,
                    "variant_ids": variant_ids  # 添加变体IDs信息
                }
                print(f"返回结果总览: {total_reviews}条评论, 平均评分: {round(avg_rating, 1)}")
                return Response(result)
            
            # 无评论时返回空数据
            result = {
                "total": 0,
                "average_rating": 0,
                "rating_counts": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
                "reviews": [],
                "original_id": product_id_int,
                "product_id": real_product_id,
                "variant_ids": variant_ids  # 添加变体IDs信息
            }
            print("无评论数据，返回空结果")
            return Response(result)
            
        except ValueError:
            print(f"无效的商品ID: {product_id}")
            return Response({
                "error": "无效的商品ID",
                "total": 0,
                "average_rating": 0,
                "rating_counts": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
                "reviews": []
            }, status=status.HTTP_400_BAD_REQUEST)

class AfterSaleRequestViewSet(viewsets.ModelViewSet):
    queryset = AfterSaleRequest.objects.all()
    serializer_class = AfterSaleRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """创建售后申请时自动关联当前用户"""
        serializer.save(user=self.request.user)
    
    def get_queryset(self):
        """只返回当前用户的售后申请"""
        return self.queryset.filter(user=self.request.user).prefetch_related('chat_messages')
    
    @action(detail=False, methods=['get'], url_path='available-items')
    def available_items(self, request):
        """获取用户可申请售后的订单商品（已完成的订单）"""
        user = request.user
        # 获取用户已完成的订单的商品，且还未申请过售后的
        order_items = OrderItem.objects.filter(
            order__user=user,
            order__status__in=['completed', 'delivered']
        ).exclude(
            after_sale_requests__isnull=False
        ).select_related('order', 'product_variant__product')
        
        items_data = []
        for item in order_items:
            items_data.append({
                'id': item.id,
                'order_id': item.order.id,
                'order_number': item.order.order_number,
                'product_name': item.product_name,
                'variant_name': item.variant_name,
                'quantity': item.quantity,
                'price': item.price,
                'order_created_at': item.order.created_at,
                'order_status': item.order.status,
            })
        
        return Response(items_data)
    
    @action(detail=False, methods=['post'], url_path='submit')
    def submit_request(self, request):
        """提交售后申请"""
        order_item_id = request.data.get('order_item_id')
        reason = request.data.get('reason')
        
        if not order_item_id or not reason:
            return Response(
                {'error': '订单商品ID和申请原因不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 验证订单商品是否属于当前用户且可以申请售后
            order_item = OrderItem.objects.get(
                id=order_item_id,
                order__user=request.user,
                order__status__in=['completed', 'delivered']
            )
            
            # 检查是否已经申请过售后
            if AfterSaleRequest.objects.filter(order_item=order_item).exists():
                return Response(
                    {'error': '该商品已经申请过售后'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 创建售后申请
            after_sale_request = AfterSaleRequest.objects.create(
                order_item=order_item,
                user=request.user,
                reason=reason,
                status='pending'
            )
            
            serializer = self.get_serializer(after_sale_request)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except OrderItem.DoesNotExist:
            return Response(
                {'error': '订单商品不存在或不可申请售后'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], url_path='send-message')
    def send_message(self, request, pk=None):
        """发送聊天消息"""
        after_sale_request = self.get_object()
        
        # 检查是否可以聊天
        if not after_sale_request.can_chat:
            return Response(
                {'error': '该售后申请已完成，无法继续聊天'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message_content = request.data.get('message', '').strip()
        if not message_content:
            return Response(
                {'error': '消息内容不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 创建消息
        chat_message = AfterSaleChatMessage.objects.create(
            after_sale_request=after_sale_request,
            sender_type='user',
            sender=request.user,
            message=message_content
        )
        
        # 更新售后申请状态为处理中（如果还是待处理状态）
        if after_sale_request.status == 'pending':
            after_sale_request.status = 'processing'
            after_sale_request.save()
        
        serializer = AfterSaleChatMessageSerializer(chat_message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'], url_path='chat-messages')
    def get_chat_messages(self, request, pk=None):
        """获取聊天消息"""
        after_sale_request = self.get_object()
        
        # 获取消息
        messages = after_sale_request.chat_messages.all()
        
        # 标记客服发送的消息为已读
        messages.filter(sender_type='admin', is_read=False).update(is_read=True)
        
        serializer = AfterSaleChatMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='mark-complete')
    def mark_complete(self, request, pk=None):
        """用户标记售后申请为完成（仅限管理员操作）"""
        after_sale_request = self.get_object()
        
        # 只有管理员才能标记为完成
        if not request.user.is_staff:
            return Response(
                {'error': '只有管理员才能执行此操作'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        after_sale_request.status = 'completed'
        after_sale_request.handler = request.user
        after_sale_request.save()
        
        return Response({'message': '售后申请已标记为完成'})

class ChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """聊天消息视图集（仅供管理员使用）"""
    queryset = AfterSaleChatMessage.objects.all()
    serializer_class = AfterSaleChatMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset.select_related('after_sale_request', 'sender')
        return AfterSaleChatMessage.objects.none()
    
    @action(detail=False, methods=['post'], url_path='admin-reply')
    def admin_reply(self, request):
        """管理员回复消息"""
        if not request.user.is_staff:
            return Response(
                {'error': '只有管理员才能执行此操作'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        after_sale_request_id = request.data.get('after_sale_request_id')
        message_content = request.data.get('message', '').strip()
        
        if not after_sale_request_id or not message_content:
            return Response(
                {'error': '售后申请ID和消息内容不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            after_sale_request = AfterSaleRequest.objects.get(id=after_sale_request_id)
            
            # 检查是否可以聊天
            if not after_sale_request.can_chat:
                return Response(
                    {'error': '该售后申请已完成，无法继续聊天'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 创建回复消息
            chat_message = AfterSaleChatMessage.objects.create(
                after_sale_request=after_sale_request,
                sender_type='admin',
                sender=request.user,
                message=message_content
            )
            
            # 设置处理人员
            if not after_sale_request.handler:
                after_sale_request.handler = request.user
                after_sale_request.save()
            
            serializer = self.get_serializer(chat_message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except AfterSaleRequest.DoesNotExist:
            return Response(
                {'error': '售后申请不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )