from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Order, OrderItem, OrderStatusHistory, OrderRefund
from decimal import Decimal

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class OrderItemSerializer(serializers.ModelSerializer):
    after_sale_requests = serializers.SerializerMethodField()
    can_request_after_sale = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ['subtotal']
        extra_kwargs = {
            'order': {'required': False}  # 添加这一行，使order字段在嵌套使用时不是必需的
        }
    
    def get_after_sale_requests(self, obj):
        """获取该商品的售后申请"""
        from apps.review.models import AfterSaleRequest
        requests = AfterSaleRequest.objects.filter(order_item=obj).values(
            'id', 'reason', 'status', 'created_at', 'updated_at'
        )
        return list(requests)
    
    def get_can_request_after_sale(self, obj):
        """检查该商品是否可以申请售后"""
        from apps.review.models import AfterSaleRequest
        # 订单必须是已完成或已送达状态，且该商品还没有售后申请
        return (obj.order.status in ['completed', 'delivered'] and 
                not AfterSaleRequest.objects.filter(order_item=obj).exists())
    
    def validate(self, data):
        # 确保数量为正数
        quantity = data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({'quantity': '商品数量必须大于0'})
        
        # 确保价格为非负数
        price = data.get('price')
        if price is not None and price < 0:
            raise serializers.ValidationError({'price': '商品价格不能为负数'})
        
        return data
    
    def to_internal_value(self, data):
        # 处理前端发送的可能不符合格式要求的数据
        if 'price' in data and not isinstance(data['price'], (int, float, Decimal)):
            try:
                data['price'] = float(data['price'])
            except (ValueError, TypeError):
                data['price'] = 0
        
        if 'quantity' in data and not isinstance(data['quantity'], int):
            try:
                data['quantity'] = int(data['quantity'])
            except (ValueError, TypeError):
                data['quantity'] = 1
        
        return super().to_internal_value(data)

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    operator_name = serializers.CharField(source='operator.username', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = '__all__'
        read_only_fields = ['created_at']

class OrderRefundSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = OrderRefund
        fields = [
            'id', 'order', 'order_number', 'refund_number', 'type', 'status', 
            'reason', 'refund_amount', 'evidence_images', 'admin_remark', 
            'processed_at', 'created_at', 'coupon_returned', 'coupon_returned_at',
            'coupon_code', 'coupon_value', 'coupon_type', 'coupon_min_amount'
        ]
        read_only_fields = ['refund_number', 'created_at', 'processed_at', 
                           'coupon_returned', 'coupon_returned_at', 
                           'coupon_code', 'coupon_value', 'coupon_type', 'coupon_min_amount']
    
    def validate_refund_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('退款金额必须大于0')
        return value
    
    def to_representation(self, instance):
        """自定义序列化表示"""
        data = super().to_representation(instance)
        
        # 添加优惠券退还状态
        if instance.coupon_returned:
            data['coupon_returned_display'] = '已退还'
        else:
            data['coupon_returned_display'] = '未退还'
        
        # 添加优惠券类型显示
        if instance.coupon_type == 'discount':
            data['coupon_type_display'] = '折扣券'
            # 将折扣值转换为百分比显示
            if instance.coupon_value:
                data['coupon_value_display'] = f"{float(instance.coupon_value) * 100}%"
        elif instance.coupon_type == 'fixed':
            data['coupon_type_display'] = '满减券'
            if instance.coupon_value:
                data['coupon_value_display'] = f"¥{float(instance.coupon_value)}"
        elif instance.coupon_type == 'free_shipping':
            data['coupon_type_display'] = '包邮券'
            data['coupon_value_display'] = '包邮'
        
        return data

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_info = UserSerializer(source='user', read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    refunds = OrderRefundSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    can_pay = serializers.BooleanField(read_only=True)
    can_confirm_receipt = serializers.BooleanField(read_only=True)
    can_request_after_sale = serializers.BooleanField(read_only=True)
    total_price = serializers.SerializerMethodField()
    recipient_info = serializers.SerializerMethodField()
    coupon_discount = serializers.SerializerMethodField()
    member_discount_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['order_number', 'created_at', 'updated_at', 'total_price', 'recipient_info', 'coupon_discount', 'member_discount_info']
    
    def get_total_price(self, obj):
        """计算总价（包含会员折扣和优惠券折扣）"""
        return float(obj.total_amount) + float(obj.shipping_fee) - float(obj.discount_amount) - float(obj.member_discount or 0)
    
    def get_recipient_info(self, obj):
        """获取收货人信息"""
        if not obj.shipping_address:
            return None
        
        return {
            'name': obj.shipping_address.get('recipient_name', ''),
            'phone': obj.shipping_address.get('recipient_phone', ''),
            'address': obj.shipping_address.get('full_address', '')
        }
    
    def get_coupon_discount(self, obj):
        """获取优惠券折扣金额"""
        # 使用discount_amount作为优惠券折扣金额
        return float(obj.discount_amount) if obj.discount_amount else 0
    
    def get_member_discount_info(self, obj):
        """获取会员折扣信息"""
        return {
            'discount_amount': float(obj.member_discount or 0),
            'discount_rate': float(obj.member_discount_rate or 1.00),
            'member_level': obj.member_level or '银卡会员',
            'discount_percentage': int((1 - float(obj.member_discount_rate or 1.00)) * 100)
        }
    
    def validate(self, data):
        # 验证价格逻辑
        total_amount = data.get('total_amount', Decimal('0.00'))
        shipping_fee = data.get('shipping_fee', Decimal('0.00'))
        discount_amount = data.get('discount_amount', Decimal('0.00'))
        
        if total_amount < 0:
            raise serializers.ValidationError('商品小计不能为负数')
        if shipping_fee < 0:
            raise serializers.ValidationError('运费不能为负数')
        if discount_amount < 0:
            raise serializers.ValidationError('优惠金额不能为负数')
        
        return data
    
    def create(self, validated_data):
        items_data = self.context.get('items_data', [])
        order = Order.objects.create(**validated_data)
        
        # 创建订单项
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        # 创建状态历史记录
        OrderStatusHistory.objects.create(
            order=order,
            to_status=order.status,
            remark='订单创建',
            operator=self.context.get('request').user if self.context.get('request') else None
        )
        
        return order
    
    def update(self, instance, validated_data):
        # 记录状态变更
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        if old_status != new_status:
            OrderStatusHistory.objects.create(
                order=instance,
                from_status=old_status,
                to_status=new_status,
                remark=validated_data.get('status_change_remark', ''),
                operator=self.context.get('request').user if self.context.get('request') else None
            )
        
        return super().update(instance, validated_data)

class OrderCreateSerializer(serializers.Serializer):
    """创建订单的序列化器"""
    items = serializers.ListField(child=serializers.DictField(), min_length=1)
    recipient_name = serializers.CharField(max_length=50)
    recipient_phone = serializers.CharField(max_length=20)
    shipping_address = serializers.JSONField()
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES)
    coupon_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    remark = serializers.CharField(required=False, allow_blank=True)
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('订单必须包含至少一个商品')
        
        # 检查每个商品是否有必要的字段
        for i, item in enumerate(value):
            if 'product_variant_id' not in item:
                raise serializers.ValidationError(f'第{i+1}个商品缺少product_variant_id字段')
            if 'quantity' not in item:
                raise serializers.ValidationError(f'第{i+1}个商品缺少quantity字段')
            if 'price' not in item:
                raise serializers.ValidationError(f'第{i+1}个商品缺少price字段')
            
            # 确保数据类型正确
            try:
                product_variant_id = int(item['product_variant_id'])
                if product_variant_id <= 0:
                    raise serializers.ValidationError(f'第{i+1}个商品的product_variant_id必须为正整数')
            except (ValueError, TypeError):
                raise serializers.ValidationError(f'第{i+1}个商品的product_variant_id必须为整数')
            
            try:
                quantity = int(item['quantity'])
                if quantity <= 0:
                    raise serializers.ValidationError(f'第{i+1}个商品的quantity必须为正整数')
            except (ValueError, TypeError):
                raise serializers.ValidationError(f'第{i+1}个商品的quantity必须为整数')
            
            try:
                price = float(item['price'])
                if price < 0:
                    raise serializers.ValidationError(f'第{i+1}个商品的price不能为负数')
            except (ValueError, TypeError):
                raise serializers.ValidationError(f'第{i+1}个商品的price必须为数字')
        
        return value
    
    def validate_shipping_address(self, value):
        """验证收货地址"""
        if not isinstance(value, dict):
            raise serializers.ValidationError('收货地址必须是JSON对象')
        
        # 检查必要的字段
        required_fields = ['province', 'city', 'district', 'detail', 'full_address']
        for field in required_fields:
            if field not in value or not value[field]:
                raise serializers.ValidationError(f'收货地址缺少{field}字段')
        
        return value
    
    def validate(self, data):
        # 添加额外的验证逻辑
        recipient_name = data.get('recipient_name')
        if not recipient_name or len(recipient_name.strip()) == 0:
            raise serializers.ValidationError({'recipient_name': '收货人姓名不能为空'})
        
        recipient_phone = data.get('recipient_phone')
        if not recipient_phone or len(recipient_phone.strip()) == 0:
            raise serializers.ValidationError({'recipient_phone': '收货人电话不能为空'})
        
        # 简单的手机号格式验证
        if recipient_phone and not recipient_phone.isdigit():
            raise serializers.ValidationError({'recipient_phone': '手机号格式不正确，应为纯数字'})
        
        return data
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        
        print("===== 订单创建开始 =====")
        print(f"用户: {user.username} (ID: {user.id})")
        print(f"商品项目数: {len(items_data)}")
        
        try:
            # 检查数据结构
            print(f"商品项目列表: {items_data}")
            for i, item in enumerate(items_data):
                print(f"商品项目 #{i+1}: {item}")
                if 'product_variant_id' not in item:
                    print(f"警告: 商品项目 #{i+1} 缺少 product_variant_id!")
                if 'quantity' not in item:
                    print(f"警告: 商品项目 #{i+1} 缺少 quantity!")
                if 'price' not in item:
                    print(f"警告: 商品项目 #{i+1} 缺少 price!")
            
            # 计算订单金额
            total_amount = sum(float(item['price']) * int(item['quantity']) for item in items_data)
            shipping_fee = Decimal('10.00')  # 固定运费，实际应根据地址计算
            discount_amount = Decimal('0.00')  # 优惠券折扣
            member_discount = Decimal('0.00')  # 会员折扣
            member_level = '银卡会员'
            member_discount_rate = Decimal('1.00')
                
            print(f"订单金额: 商品总额={total_amount}, 运费={shipping_fee}, 优惠券折扣={discount_amount}")
            
            # 计算会员折扣
            try:
                from apps.member.models import Member
                from apps.member.services import MemberDiscountService
                
                member = Member.objects.get(user=user)
                member_discount, member_discount_rate, member_level = MemberDiscountService.calculate_member_discount(
                    member, total_amount
                )
                print(f"会员折扣: 等级={member_level}, 折扣率={member_discount_rate}, 折扣金额={member_discount}")
                
            except Member.DoesNotExist:
                print(f"用户 {user.username} 没有会员资料，使用默认折扣")
            except Exception as e:
                print(f"计算会员折扣失败: {str(e)}")
        
            # 处理优惠券
            coupon_code = validated_data.pop('coupon_code', '')
            coupon_id = self.context['request'].data.get('coupon_id')
                
            print(f"优惠券信息: 优惠码={coupon_code}, 优惠券ID={coupon_id}")
        
            # 如果提供了优惠券信息，应用优惠券折扣
            if coupon_code or coupon_id:
                try:
                    # 优先使用coupon_id查找会员优惠券
                    if coupon_id:
                        from apps.member.models import MemberCoupon, Member
                        try:
                            print(f"尝试获取会员: user_id={user.id}")
                            member = Member.objects.get(user=user)
                            print(f"获取到会员: member_id={member.id}")
                                
                            print(f"尝试获取会员优惠券: coupon_id={coupon_id}, member_id={member.id}")
                            member_coupon = MemberCoupon.objects.get(id=coupon_id, member=member)
                            coupon = member_coupon.coupon
                                
                            print(f"获取到会员优惠券: coupon.name={coupon.name}, coupon.type={coupon.type}")
                            
                            # 验证优惠券
                            if member_coupon.status != 'available':
                                print(f"优惠券状态不可用: {member_coupon.status}")
                                raise serializers.ValidationError('该优惠券不可用')
                            
                            if coupon.min_amount and total_amount < float(coupon.min_amount):
                                print(f"订单金额不满足优惠券使用条件: 订单金额={total_amount}, 最低要求={coupon.min_amount}")
                                raise serializers.ValidationError(f'订单金额不满足优惠券使用条件，最低需要¥{float(coupon.min_amount)}')
                            
                            # 计算折扣金额
                            if coupon.type == 'fixed':  # 满减券
                                discount_amount = Decimal(str(coupon.value))
                                print(f"应用满减券: 减免金额={discount_amount}")
                            elif coupon.type == 'discount':  # 折扣券
                                discount_value = Decimal(str(coupon.value))
                                # 将total_amount转换为Decimal类型，避免类型不匹配错误
                                total_amount_decimal = Decimal(str(total_amount))
                                discount_amount = total_amount_decimal * (Decimal('1.0') - discount_value)
                                # 检查最大折扣限制
                                if coupon.max_discount and discount_amount > Decimal(str(coupon.max_discount)):
                                    discount_amount = Decimal(str(coupon.max_discount))
                                print(f"应用折扣券: 折扣率={discount_value}, 减免金额={discount_amount}")
                            elif coupon.type == 'free_shipping':  # 包邮券
                                discount_amount = shipping_fee
                                print(f"应用包邮券: 减免运费={discount_amount}")
                            
                            # 不再标记优惠券为已使用，只在订单支付成功后才标记
                            print(f"优惠券折扣应用成功: ID={coupon_id}, 折扣金额={discount_amount}")
                            
                        except (Member.DoesNotExist, MemberCoupon.DoesNotExist) as e:
                            print(f"查找会员优惠券失败: {str(e)}")
                    
                    # 如果没有通过ID找到优惠券，尝试使用优惠码
                    elif coupon_code:
                        from apps.coupon.models import Coupon
                        try:
                            print(f"尝试通过优惠码查找优惠券: {coupon_code}")
                            coupon = Coupon.objects.get(code=coupon_code)
                            
                            # 验证优惠券
                            from django.utils import timezone
                            now = timezone.now()
                            if not (coupon.start_time <= now <= coupon.end_time):
                                print(f"优惠券已过期: start={coupon.start_time}, end={coupon.end_time}, now={now}")
                                raise serializers.ValidationError('优惠券已过期')
                            
                            if total_amount < float(coupon.min_purchase_amount):
                                print(f"订单金额不满足使用条件: 订单金额={total_amount}, 最低要求={coupon.min_purchase_amount}")
                                raise serializers.ValidationError(f'订单金额不满足使用条件，最低需要¥{coupon.min_purchase_amount}')
                            
                            # 计算折扣金额
                            if coupon.coupon_type == 'full_reduction':
                                discount_amount = Decimal(str(coupon.discount_amount))
                                print(f"应用满减券: 减免金额={discount_amount}")
                            elif coupon.coupon_type == 'discount':
                                # 将total_amount转换为Decimal类型，避免类型不匹配错误
                                total_amount_decimal = Decimal(str(total_amount))
                                discount_amount = total_amount_decimal * (Decimal('1.0') - Decimal(str(coupon.discount_rate)))
                                print(f"应用折扣券: 折扣率={coupon.discount_rate}, 减免金额={discount_amount}")
                            elif coupon.coupon_type == 'free_shipping':
                                discount_amount = shipping_fee
                                print(f"应用包邮券: 减免运费={discount_amount}")
                            
                        except Coupon.DoesNotExist:
                            print(f"优惠码不存在: {coupon_code}")
                
                except Exception as e:
                    print(f"应用优惠券失败: {str(e)}")
            
            # 获取收货信息
            recipient_name = validated_data.pop('recipient_name')
            recipient_phone = validated_data.pop('recipient_phone')
            shipping_address = validated_data.pop('shipping_address')
                
            print(f"收货信息: 收货人={recipient_name}, 电话={recipient_phone}, 地址={shipping_address}")
            
            # 添加收货人信息到shipping_address
            shipping_address['recipient_name'] = recipient_name
            shipping_address['recipient_phone'] = recipient_phone
            
            # 创建订单
            order_data = {
                'user': user,
                'total_amount': Decimal(str(total_amount)),
                'shipping_fee': shipping_fee,
                'discount_amount': discount_amount,
                'member_discount': member_discount,
                'member_level': member_level,
                'member_discount_rate': member_discount_rate,
                'shipping_address': shipping_address,
                'payment_method': validated_data.get('payment_method'),
                'remark': validated_data.get('remark', ''),
            }
            
            print(f"创建订单数据: {order_data}")
            order = Order.objects.create(**order_data)
            print(f"订单创建成功: ID={order.id}, 订单号={order.order_number}")
                
            # 创建订单项
            for item_data in items_data:
                # 确保数据类型正确
                try:
                    from apps.product.models import ProductVariant
                    
                    product_variant_id = int(item_data['product_variant_id'])
                    quantity = int(item_data['quantity'])
                    price = Decimal(str(item_data['price']))
                    
                    print(f"处理订单项: 商品变体ID={product_variant_id}, 数量={quantity}, 价格={price}")
                    
                    # 获取商品变体信息
                    try:
                        product_variant = ProductVariant.objects.get(id=product_variant_id)
                        product_name = product_variant.product.name
                        variant_name = product_variant.name
                        print(f"获取到商品信息: 产品名={product_name}, 变体名={variant_name}")
                    except ProductVariant.DoesNotExist:
                        product_name = item_data.get('product_name', f'商品变体 {product_variant_id}')
                        variant_name = item_data.get('variant_name', '')
                        print(f"商品变体不存在，使用默认值: 产品名={product_name}, 变体名={variant_name}")
                    
                    # 创建订单项
                    order_item = OrderItem.objects.create(
                        order=order,
                        product_variant_id=product_variant_id,
                        product_name=product_name,
                        variant_name=variant_name,
                        price=price,
                        quantity=quantity,
                        subtotal=price * quantity
                    )
                    print(f"订单项创建成功: ID={order_item.id}, 小计={order_item.subtotal}")
                except Exception as e:
                    print(f"创建订单项失败: {str(e)}")
                    raise serializers.ValidationError(f"创建订单项失败: {str(e)}")
                
            # 创建状态历史
            order_history = OrderStatusHistory.objects.create(
                order=order,
                to_status='pending',
                remark='订单创建',
                operator=user
            )
            print(f"订单状态历史创建成功: ID={order_history.id}")
            
            # 如果使用了优惠券，将优惠券ID关联到订单，但不标记为已使用
            # 只有在订单支付成功后，才会真正标记优惠券为已使用
            if coupon_id:
                try:
                    # 将使用的优惠券ID存储在订单的meta数据中
                    if not order.meta:
                        order.meta = {}
                    order.meta['coupon_id'] = coupon_id
                    order.meta['coupon_used'] = False  # 标记优惠券尚未实际使用
                    
                    # 保存优惠券类型和代码信息
                    if 'coupon' in locals():
                        order.meta['coupon_type'] = coupon.type
                        order.meta['coupon_code'] = coupon.code
                    
                    order.save(update_fields=['meta'])
                    
                    print(f"优惠券 ID={coupon_id} 已关联到订单，但尚未标记为已使用")
                    
                except Exception as e:
                    print(f"关联优惠券到订单时出错: {str(e)}")
            elif coupon_code:
                try:
                    # 将使用的优惠券代码存储在订单的meta数据中
                    if not order.meta:
                        order.meta = {}
                    order.meta['coupon_code'] = coupon_code
                    
                    # 保存优惠券类型信息
                    if 'coupon' in locals():
                        order.meta['coupon_type'] = coupon.coupon_type
                    
                    order.save(update_fields=['meta'])
                    
                    print(f"优惠券代码 {coupon_code} 已关联到订单")
                except Exception as e:
                    print(f"关联优惠券代码到订单时出错: {str(e)}")
            
            # 清空用户购物车
            from apps.cart.models import Cart
            try:
                cart = Cart.objects.get(user=user)
                cart.clear()
                print(f"已清空用户购物车")
            except Cart.DoesNotExist:
                print(f"用户没有购物车记录")
                pass
            
            print("===== 订单创建完成 =====")
            return order
        except Exception as e:
            print(f"===== 订单创建失败: {str(e)} =====")
            import traceback
            traceback.print_exc()
            raise serializers.ValidationError(f"创建订单失败: {str(e)}")