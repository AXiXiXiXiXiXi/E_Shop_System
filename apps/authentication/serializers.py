from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.apps import apps
from django.contrib.auth.hashers import check_password


class LoginSerializer(serializers.Serializer):
    """用户登录序列化器"""
    username = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20, required=False)
    password = serializers.CharField(max_length=128, write_only=True)
    login_type = serializers.CharField(max_length=10, required=False, default='username')  # username, email, phone
    
    def validate(self, attrs):
        login_type = attrs.get('login_type', 'username')
        password = attrs.get('password')
        
        if not password:
            raise serializers.ValidationError('必须提供密码')
            
        if login_type == 'username':
            username = attrs.get('username')
            if not username:
                raise serializers.ValidationError('使用用户名登录时必须提供用户名')
            try:
                # 通过用户名查询用户
                user = User.objects.filter(username=username).first()
                if not user:
                    raise serializers.ValidationError('用户名不存在')
            except Exception:
                raise serializers.ValidationError('用户名或密码错误')
        
        elif login_type == 'email':
            email = attrs.get('email')
            if not email:
                raise serializers.ValidationError('使用邮箱登录时必须提供邮箱')
            try:
                # 通过邮箱查询用户
                user = User.objects.filter(email=email).first()
                if not user:
                    raise serializers.ValidationError('该邮箱未注册')
            except Exception:
                raise serializers.ValidationError('邮箱或密码错误')
        
        elif login_type == 'phone':
            phone = attrs.get('phone')
            if not phone:
                raise serializers.ValidationError('使用手机号登录时必须提供手机号')
                
            # 清除所有非数字字符
            phone = ''.join(filter(str.isdigit, phone))
            
            try:
                # 尝试获取Member模型
                Member = apps.get_model('member', 'Member')
                # 通过手机号查询会员
                member = Member.objects.filter(phone=phone).first()
                if not member:
                    raise serializers.ValidationError('该手机号未注册')
                user = member.user
            except Exception as e:
                print(f"手机号登录查询出错: {e}")
                raise serializers.ValidationError('手机号或密码错误')
        else:
            raise serializers.ValidationError('不支持的登录方式')
        
        # 验证密码
        if user and check_password(password, user.password):
            if not user.is_active:
                raise serializers.ValidationError('用户账户已被禁用')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('密码错误')
        
        return attrs


class RegisterSerializer(serializers.Serializer):
    """用户注册序列化器"""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(max_length=128, write_only=True)
    password_confirm = serializers.CharField(max_length=128, write_only=True)
    phone = serializers.CharField(max_length=20, required=False)  # 添加手机号字段
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('用户名已存在')
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('邮箱已被注册')
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError('两次输入的密码不一致')
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        # 获取phone字段，确保是字符串类型，且只有数字
        phone_str = validated_data.get('phone', '')
        # 清除所有非数字字符
        phone = ''.join(filter(str.isdigit, phone_str)) if phone_str else ''
        
        # 确保phone不为空
        if not phone:
            phone = '00000000000'  # 默认值，11个0
        
        # 由于数据库的phone字段不能为空，我们需要使用Django内部方式创建用户
        from django.db import connection
        with connection.cursor() as cursor:
            # 1. 创建用户基本信息
            username = validated_data.get('username')
            email = validated_data.get('email')
            password = validated_data.get('password')
            
            # 2. 使用内置方法生成加密密码
            from django.contrib.auth.hashers import make_password
            hashed_password = make_password(password)
            
            # 3. 插入用户数据
            cursor.execute(
                """
                INSERT INTO auth_user 
                (username, email, password, is_superuser, is_staff, is_active, date_joined, first_name, last_name, phone)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s)
                """,
                [
                    username, 
                    email, 
                    hashed_password, 
                    False,  # is_superuser 
                    False,  # is_staff
                    True,   # is_active
                    '',     # first_name
                    '',     # last_name
                    phone   # phone
                ]
            )
            
            # 4. 获取用户ID
            cursor.execute("SELECT LAST_INSERT_ID()")
            user_id = cursor.fetchone()[0]
            
            # 5. 获取用户对象
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            
            # 6. 直接在数据库中创建member记录
            try:
                cursor.execute(
                    """
                    INSERT INTO member_member 
                    (user_id, phone, points, growth_value, balance, total_orders, total_spent, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    [
                        user_id,  # user_id
                        phone,    # phone
                        0,        # points
                        0,        # growth_value
                        0.00,     # balance
                        0,        # total_orders
                        0.00      # total_spent
                    ]
                )
                print(f"成功创建Member记录，用户ID: {user_id}")
            except Exception as e:
                print(f"创建Member记录失败，但用户注册仍然成功，用户ID: {user_id}, 错误: {e}")
        
        # 仍然尝试使用Django ORM创建Member记录作为备份措施
        try:
            # 使用Django的apps机制获取Member模型
            Member = apps.get_model('member', 'Member')
            # 检查Member记录是否已经存在
            if not Member.objects.filter(user=user).exists():
                Member.objects.create(
                    user=user,
                    phone=phone  # 将phone保存到Member模型
                )
        except Exception as e:
            # 如果Member创建失败，记录错误但不阻止用户创建
            print(f"ORM创建会员信息时出错: {e}")
        
        # 为新用户发放所有可用优惠券
        try:
            from apps.member.signals import auto_issue_all_coupons_to_new_member
            member = Member.objects.filter(user=user).first()
            if member:
                auto_issue_all_coupons_to_new_member(member.id, user.username)
                print(f"已为新用户 {user.username} 自动发放优惠券")
            else:
                print(f"警告：无法为用户 {user.username} 发放优惠券，因为Member记录不存在")
        except Exception as e:
            print(f"为新用户 {user.username} 发放优惠券失败: {e}")
        
        return user


class UserSerializer(serializers.ModelSerializer):
    """用户信息序列化器"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']