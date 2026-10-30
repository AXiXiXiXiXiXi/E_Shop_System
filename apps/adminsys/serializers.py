from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from .models import Role, AdminUser, Permission

class RoleSerializer(serializers.ModelSerializer):
    """角色序列化器"""
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description', 'is_active', 'created_at'
        ]
        extra_kwargs = {
            'name': {'help_text': '角色名称，如：超级管理员、普通管理员'},
            'description': {'help_text': '角色描述，说明该角色的职责范围'},
        }

class AdminUserCreateSerializer(serializers.ModelSerializer):
    """管理员用户创建序列化器"""
    password = serializers.CharField(
        write_only=True, 
        min_length=8,
        help_text="密码至少8位，包含字母和数字"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        help_text="确认密码"
    )
    role_name = serializers.ReadOnlyField()
    
    class Meta:
        model = AdminUser
        fields = [
            'id', 'username', 'password', 'password_confirm', 'email', 
            'phone', 'real_name', 'role', 'role_name', 'is_active'
        ]
        extra_kwargs = {
            'username': {'help_text': '用户名，3-20位字母数字下划线'},
            'email': {'help_text': '邮箱地址，用于接收通知'},
            'phone': {'help_text': '手机号，11位数字'},
            'real_name': {'help_text': '真实姓名'},
        }
    
    def validate(self, attrs):
        """验证数据"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "两次密码输入不一致"})
        
        # 移除确认密码字段
        attrs.pop('password_confirm', None)
        return attrs
    
    def create(self, validated_data):
        """创建管理员用户"""
        password = validated_data.pop('password')
        user = AdminUser(**validated_data)
        
        try:
            user.set_password(password)
            user.full_clean()  # 调用模型验证
            user.save()
            return user
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)

class AdminUserSerializer(serializers.ModelSerializer):
    """管理员用户序列化器（列表/详情）"""
    role_name = serializers.ReadOnlyField()
    created_at_local = serializers.SerializerMethodField(help_text="本地时间格式的创建时间")
    updated_at_local = serializers.SerializerMethodField(help_text="本地时间格式的更新时间")
    last_login_local = serializers.SerializerMethodField(help_text="本地时间格式的最后登录时间")
    
    class Meta:
        model = AdminUser
        fields = [
            'id', 'username', 'email', 'phone', 'real_name', 'role', 
            'role_name', 'is_active', 'last_login', 'login_count',
            'created_at', 'updated_at', 'created_at_local', 'updated_at_local', 'last_login_local'
        ]
        read_only_fields = ['last_login', 'login_count', 'created_at', 'updated_at']
    
    def get_created_at_local(self, obj):
        """获取本地时间格式的创建时间"""
        if obj.created_at:
            return timezone.localtime(obj.created_at).strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    def get_updated_at_local(self, obj):
        """获取本地时间格式的更新时间"""
        if obj.updated_at:
            return timezone.localtime(obj.updated_at).strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    def get_last_login_local(self, obj):
        """获取本地时间格式的最后登录时间"""
        if obj.last_login:
            return timezone.localtime(obj.last_login).strftime('%Y-%m-%d %H:%M:%S')
        return None

class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """管理员用户更新序列化器"""
    role_name = serializers.ReadOnlyField()
    
    class Meta:
        model = AdminUser
        fields = [
            'id', 'email', 'phone', 'real_name', 'role', 'role_name', 'is_active'
        ]
        extra_kwargs = {
            'email': {'help_text': '邮箱地址'},
            'phone': {'help_text': '手机号'},
            'real_name': {'help_text': '真实姓名'},
        }
    
    def update(self, instance, validated_data):
        """更新用户信息"""
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.full_clean()
            instance.save()
            return instance
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)

class PasswordChangeSerializer(serializers.Serializer):
    """密码修改序列化器"""
    old_password = serializers.CharField(write_only=True, help_text="当前密码")
    new_password = serializers.CharField(
        write_only=True, 
        min_length=8,
        help_text="新密码，至少8位包含字母和数字"
    )
    new_password_confirm = serializers.CharField(write_only=True, help_text="确认新密码")
    
    def validate(self, attrs):
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError({"new_password_confirm": "两次新密码输入不一致"})
        
        return attrs
    
    def validate_old_password(self, value):
        """验证旧密码"""
        user = self.context['user']
        if not user.check_password(value):
            raise serializers.ValidationError("当前密码错误")
        return value

class PermissionSerializer(serializers.ModelSerializer):
    """权限序列化器"""
    role_count = serializers.ReadOnlyField()
    created_at_local = serializers.SerializerMethodField(help_text="本地时间格式的创建时间")
    
    class Meta:
        model = Permission
        fields = [
            'id', 'name', 'codename', 'description', 'module', 
            'is_active', 'created_at', 'created_at_local', 'role_count'
        ]
        extra_kwargs = {
            'name': {'help_text': '权限名称，如：查看用户列表'},
            'codename': {'help_text': '权限代码，如：view_user'},
            'description': {'help_text': '权限详细描述'},
            'module': {'help_text': '所属模块，如：user、order、product'},
        }
    
    def get_created_at_local(self, obj):
        """获取本地时间格式的创建时间"""
        if obj.created_at:
            return timezone.localtime(obj.created_at).strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    def validate_codename(self, value):
        """验证权限代码"""
        if not value.strip():
            raise serializers.ValidationError("权限代码不能为空")
        return value.strip().lower()
    
    def validate_name(self, value):
        """验证权限名称"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("权限名称至少2个字符")
        return value.strip()