from rest_framework import serializers
from .models import PasswordResetRequest
from django.contrib.auth.models import User

class PasswordResetRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordResetRequest
        fields = [
            'username', 'phone', 'email', 'first_name', 'last_name', 
            'reason', 'new_password'
        ]
    
    def validate_email(self, value):
        """验证邮箱格式"""
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise serializers.ValidationError('邮箱格式不正确')
        return value
    
    def validate_phone(self, value):
        """验证手机号格式"""
        import re
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式不正确')
        return value
    
    def validate_new_password(self, value):
        """验证密码强度"""
        if len(value) < 6:
            raise serializers.ValidationError('密码至少需要6个字符')
        if len(value) > 20:
            raise serializers.ValidationError('密码不能超过20个字符')
        return value
    
    def validate(self, attrs):
        """整体验证"""
        # 检查是否有重复的待处理请求
        existing_request = PasswordResetRequest.objects.filter(
            username=attrs['username'],
            email=attrs['email'],
            status='pending'
        ).first()
        
        if existing_request:
            raise serializers.ValidationError(
                f'您已有一个待处理的密码重置请求，提交时间：{existing_request.created_at.strftime("%Y-%m-%d %H:%M:%S")}'
            )
        
        return attrs

class PasswordResetRequestListSerializer(serializers.ModelSerializer):
    """用于管理员查看的序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    matched_user_username = serializers.CharField(source='matched_user.username', read_only=True)
    processed_by_username = serializers.CharField(source='processed_by.username', read_only=True)
    
    class Meta:
        model = PasswordResetRequest
        fields = [
            'id', 'username', 'phone', 'email', 'first_name', 'last_name',
            'reason', 'status', 'status_display', 'created_at', 'updated_at',
            'matched_user_username', 'processed_by_username', 'processed_at',
            'admin_notes', 'client_ip'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at'] 