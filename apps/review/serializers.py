from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Review, AfterSaleRequest, AfterSaleChatMessage
from apps.order.models import OrderItem

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'product_id', 'product_name', 'rating', 'content', 
                  'images', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("评分必须在1-5之间")
        return value

class AfterSaleChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AfterSaleChatMessage
        fields = ['id', 'sender_type', 'sender', 'sender_name', 'message', 'is_read', 'created_at']
        read_only_fields = ['id', 'sender_type', 'sender', 'sender_name', 'created_at']
    
    def get_sender_name(self, obj):
        if obj.sender_type == 'admin':
            return f"客服 {obj.sender.first_name or obj.sender.username}"
        return obj.sender.username

class AfterSaleRequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    handler = UserSerializer(read_only=True)
    order_item_details = serializers.SerializerMethodField()
    chat_messages = AfterSaleChatMessageSerializer(many=True, read_only=True)
    unread_count = serializers.SerializerMethodField()
    can_chat = serializers.ReadOnlyField()
    
    class Meta:
        model = AfterSaleRequest
        fields = ['id', 'user', 'order_item', 'order_item_details', 'reason', 'status', 
                  'handler', 'created_at', 'updated_at', 'chat_messages', 'unread_count', 'can_chat']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'chat_messages', 'unread_count', 'can_chat']
    
    def get_order_item_details(self, obj):
        return {
            'id': obj.order_item.id,
            'order_number': obj.order_item.order.order_number,
            'product_name': obj.order_item.product_name,
            'variant_name': obj.order_item.variant_name,
            'quantity': obj.order_item.quantity,
            'price': obj.order_item.price
        }
    
    def get_unread_count(self, obj):
        # 获取用户未读的消息数量（客服发送的未读消息）
        request = self.context.get('request')
        if request and request.user:
            return obj.chat_messages.filter(
                sender_type='admin',
                is_read=False
            ).count()
        return 0