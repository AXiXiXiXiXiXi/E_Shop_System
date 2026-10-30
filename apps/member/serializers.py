from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    MemberLevel, Member, PointsHistory, Address, 
    Coupon, MemberCoupon, SignInRecord, RechargeRecord
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class MemberLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberLevel
        fields = [
            'id', 'name', 'points_threshold', 'discount_rate', 
            'icon', 'description', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PointsHistorySerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    member_name = serializers.CharField(source='member.user.username', read_only=True)
    
    class Meta:
        model = PointsHistory
        fields = [
            'id', 'member', 'member_name', 'points', 
            'type', 'type_display', 'description', 
            'order_id', 'admin_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class AddressSerializer(serializers.ModelSerializer):
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Address
        fields = [
            'id', 'name', 'phone', 'province', 
            'city', 'district', 'detail', 
            'is_default', 'full_address', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_address']
    
    def get_full_address(self, obj):
        return f"{obj.province} {obj.city} {obj.district} {obj.detail}"
    
    def to_representation(self, instance):
        # 确保is_default字段被序列化为布尔值
        representation = super().to_representation(instance)
        representation['is_default'] = bool(instance.is_default)
        return representation

class CouponSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'name', 'code', 'type', 'type_display', 'value', 
            'min_amount', 'max_discount', 'usage_limit', 'used_count', 
            'status', 'status_display', 'is_available', 'start_date', 
            'end_date', 'created_at'
        ]
        read_only_fields = ['id', 'used_count', 'created_at', 'is_available']

class MemberCouponSerializer(serializers.ModelSerializer):
    coupon = CouponSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = MemberCoupon
        fields = [
            'id', 'coupon', 'status', 'status_display', 'is_available',
            'obtained_at', 'used_at', 'order_id'
        ]
        read_only_fields = ['id', 'obtained_at', 'is_available']

class SignInRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignInRecord
        fields = [
            'id', 'sign_in_date', 'points_earned', 'consecutive_days'
        ]
        read_only_fields = ['id', 'sign_in_date']

class MemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    level_name = serializers.SerializerMethodField(read_only=True)
    next_level_points = serializers.SerializerMethodField()
    current_level_points = serializers.SerializerMethodField()
    max_level_points = serializers.SerializerMethodField()
    
    # 添加积分历史和优惠券字段，用于详情页
    points_history = serializers.SerializerMethodField(read_only=True)
    
    # 明确定义phone字段，确保它被包含在序列化输出中
    phone = serializers.CharField(required=False, allow_blank=True)
    
    # 添加first_name和last_name字段支持
    first_name = serializers.CharField(required=False, allow_blank=True, write_only=True)
    last_name = serializers.CharField(required=False, allow_blank=True, write_only=True)
    
    class Meta:
        model = Member
        fields = [
            'id', 'user', 'level', 'level_name', 'points', 'growth_value', 
            'balance', 'avatar', 'phone', 'birthday', 'gender', 
            'total_orders', 'total_spent', 'created_at', 'updated_at',
            'next_level_points', 'current_level_points', 'max_level_points',
            'points_history', 'first_name', 'last_name'
        ]
        read_only_fields = [
            'id', 'user', 'points', 'total_orders', 
            'total_spent', 'created_at', 'updated_at', 
            'next_level_points', 'current_level_points', 'max_level_points',
            'points_history'
        ]
    
    def update(self, instance, validated_data):
        """自定义更新方法，处理用户表的first_name和last_name字段"""
        # 提取first_name和last_name
        first_name = validated_data.pop('first_name', None)
        last_name = validated_data.pop('last_name', None)
        
        # 更新Member模型的字段
        instance = super().update(instance, validated_data)
        
        # 更新关联的User模型的first_name和last_name字段
        if first_name is not None or last_name is not None:
            user = instance.user
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            user.save()
        
        return instance
    
    def get_level_name(self, obj):
        """根据字符串level获取等级名称"""
        from .services import MemberLevelService
        try:
            # 获取会员等级名称
            level = MemberLevel.objects.filter(name=obj.level, is_active=True).first()
            return level.name if level else obj.level
        except:
            return obj.level
    
    def get_points_history(self, obj):
        """获取最近的积分历史记录"""
        # 只返回最近5条记录
        history = PointsHistory.objects.filter(member=obj).order_by('-created_at')[:5]
        return PointsHistorySerializer(history, many=True).data
    
    def get_next_level_points(self, obj):
        from .services import MemberLevelService
        level_info = MemberLevelService.get_next_level_info(obj)
        return level_info['points_needed']
    
    def get_current_level_points(self, obj):
        return obj.points
    
    def get_max_level_points(self, obj):
        from .services import MemberLevelService
        level_info = MemberLevelService.get_next_level_info(obj)
        return level_info['next_level_points'] or 0

class MemberDetailSerializer(MemberSerializer):
    """会员详细信息序列化器，包含更多关联数据"""
    addresses = AddressSerializer(many=True, read_only=True)
    
    class Meta(MemberSerializer.Meta):
        fields = MemberSerializer.Meta.fields + ['addresses']

class RechargeRecordSerializer(serializers.ModelSerializer):
    """充值记录序列化器"""
    member_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = RechargeRecord
        fields = ['id', 'member', 'member_name', 'amount', 'status', 'status_display', 
                  'payment_method', 'transaction_id', 'remark', 'created_at', 'updated_at']
        read_only_fields = ['id', 'member_name', 'status_display', 'created_at', 'updated_at']
    
    def get_member_name(self, obj):
        return obj.member.user.username if obj.member and obj.member.user else ''
    
    def get_status_display(self, obj):
        return obj.get_status_display()