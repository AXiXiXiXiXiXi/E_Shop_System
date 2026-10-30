from rest_framework import serializers
from .models import Coupon, CouponUsageRecord
from apps.member.models import Member, MemberCoupon
from apps.member.models import Coupon as MemberCoupon_Coupon
from django.utils import timezone

class CouponSerializer(serializers.ModelSerializer):
    """优惠券序列化器"""
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'coupon_type', 'discount_amount', 'discount_rate', 
                  'min_purchase_amount', 'start_time', 'end_time', 'is_platform']
        read_only_fields = ['id']

class MemberCouponCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberCoupon_Coupon
        fields = ['id', 'name', 'code', 'type', 'value', 'min_amount', 'max_discount', 'start_date', 'end_date']

class MemberCouponSerializer(serializers.ModelSerializer):
    coupon_detail = MemberCouponCouponSerializer(source='coupon', read_only=True)
    status = serializers.SerializerMethodField()
    expiry_date = serializers.SerializerMethodField()
    
    class Meta:
        model = MemberCoupon
        fields = ['id', 'member', 'coupon', 'coupon_detail', 'status', 'used_at', 'order_id', 'expiry_date']
        read_only_fields = ['used_at']
    
    def get_status(self, obj):
        """获取优惠券状态"""
        now = timezone.now()
        # 优先使用数据库中的status字段
        if obj.status == 'used':
            return 'used'
        elif obj.status == 'available' and obj.used_at:
            # 如果状态为available但used_at不为空，说明优惠券已被退还
            return 'available'
        elif obj.status == 'available':
            # 如果数据库状态为available，则保持为available，即使过期时间已过
            return 'available'
        elif obj.coupon.end_date < now:
            return 'expired'
        else:
            return obj.status or 'available'
    
    def get_expiry_date(self, obj):
        """获取优惠券过期时间"""
        return obj.coupon.end_date

class CouponUsageRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponUsageRecord
        fields = ['id', 'member_id', 'coupon', 'order_id', 'coupon_code', 'coupon_type', 'discount_amount', 'used_at']
        read_only_fields = ['used_at']