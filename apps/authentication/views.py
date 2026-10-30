from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import login, authenticate
from django.utils import timezone
from django.contrib.auth.models import User
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
import logging

# 创建日志记录器
logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """用户登录"""
    try:
        # 安全地记录请求数据
        login_type = request.data.get('login_type', 'username')
        
        if login_type == 'username':
            identifier = request.data.get('username', '')
            logger.info(f"收到用户名登录请求: 用户名={identifier}")
        elif login_type == 'email':
            identifier = request.data.get('email', '')
            logger.info(f"收到邮箱登录请求: 邮箱={identifier}")
        elif login_type == 'phone':
            identifier = request.data.get('phone', '')
            logger.info(f"收到手机号登录请求: 手机号={identifier}")
        else:
            logger.info(f"收到未知类型登录请求: {login_type}")
            
        print(f"收到登录请求: 类型={login_type}, 标识符={identifier}")
    except Exception as e:
        logger.error(f"记录登录请求时出错: {e}")
    
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data.get('user')
        if not user:
            logger.error("验证成功但未返回用户对象")
            return Response({"error": "系统错误"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 确保user是User类型
        if not isinstance(user, User):
            logger.error(f"返回的用户对象类型错误: {type(user)}")
            return Response({"error": "系统错误"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 更新最后登录时间
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # 生成JWT token
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # 准备响应数据
        user_data = UserSerializer(user).data
        response_data = {
            'message': '登录成功',
            'access': str(access_token),
            'refresh': str(refresh),
            'user': user_data
        }
        
        # 安全地记录响应数据（不包含敏感信息）
        logger.info(f"登录成功: {user.username}")
        print(f"登录成功: {user.username}")
        return Response(response_data)
    
    logger.error(f"登录失败: {serializer.errors}")
    print(f"登录失败: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """用户注册"""
    try:
        # 安全地记录请求数据
        username = request.data.get('username', '')
        email = request.data.get('email', '')
        logger.info(f"收到注册请求: 用户名={username}, 邮箱={email}")
    except Exception as e:
        logger.error(f"记录注册请求时出错: {e}")
    
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # 确保user是User类型
        if not isinstance(user, User):
            logger.error(f"返回的用户对象类型错误: {type(user)}")
            return Response({"error": "系统错误"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 生成JWT token
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        response_data = {
            'message': '注册成功',
            'access': str(access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }
        logger.info(f"注册成功: {user.username}")
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    logger.error(f"注册失败: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """修改密码"""
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    # 检查参数是否完整
    if not old_password or not new_password:
        return Response(
            {'error': '请提供旧密码和新密码'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    # 验证旧密码是否正确
    if not authenticate(username=user.username, password=old_password):
        return Response(
            {'error': '原密码错误'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    # 检查新密码的复杂度
    if len(new_password) < 8:
        return Response(
            {'error': '新密码长度至少为8位'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    # 修改密码
    user.set_password(new_password)
    user.save()
    
    # 生成新的JWT token
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    
    logger.info(f"用户 {user.username} 成功修改密码")
    return Response({
        'message': '密码修改成功',
        'access': str(access_token),
        'refresh': str(refresh),
    })


class CustomTokenRefreshView(TokenRefreshView):
    """自定义token刷新视图"""
    pass


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
    """获取用户信息"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """用户登出"""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        logger.info(f"用户 {request.user.username} 登出成功")
        return Response({'message': '登出成功'})
    except Exception as e:
        logger.error(f"用户登出失败: {e}")
        return Response({'error': '登出失败'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_view(request):
    """发送重置密码邮件"""
    try:
        email = request.data.get('email')
        if not email:
            return Response({'error': '请提供邮箱地址'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证邮箱格式
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return Response({'error': '邮箱格式不正确'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查用户是否存在
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # 为了安全，即使用户不存在也返回成功信息
            logger.info(f"尝试重置不存在的邮箱: {email}")
            return Response({'message': '如果该邮箱已注册，您将收到重置密码的邮件'})
        
        # 生成重置令牌（这里使用简单的实现，实际项目应该使用更安全的方法）
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # 在实际项目中，这里应该发送邮件
        # 现在只是模拟成功
        logger.info(f"生成重置密码令牌 - 用户: {user.username}, UID: {uid}, Token: {token}")
        
        # 将令牌信息存储到缓存或数据库中（演示用）
        from django.core.cache import cache
        cache_key = f"password_reset_{user.pk}"
        cache.set(cache_key, token, timeout=3600)  # 1小时有效期
        
        return Response({
            'message': '重置密码链接已发送到您的邮箱',
            'reset_url': f'/forgot-password?token={token}&uid={uid}',  # 演示用
        })
        
    except Exception as e:
        logger.error(f"发送重置密码邮件失败: {e}")
        return Response({'error': '发送邮件失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_view(request):
    """重置密码"""
    try:
        token = request.data.get('token')
        password = request.data.get('password')
        uid = request.data.get('uid')
        
        if not all([token, password, uid]):
            return Response({'error': '缺少必要参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证密码强度
        if len(password) < 6:
            return Response({'error': '密码至少需要6个字符'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 解码用户ID
        from django.utils.http import urlsafe_base64_decode
        from django.utils.encoding import force_str
        
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': '无效的重置链接'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证令牌
        from django.contrib.auth.tokens import default_token_generator
        from django.core.cache import cache
        
        # 从缓存中获取令牌
        cache_key = f"password_reset_{user.pk}"
        cached_token = cache.get(cache_key)
        
        if not cached_token or cached_token != token:
            return Response({'error': '重置链接无效或已过期'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证Django的默认令牌
        if not default_token_generator.check_token(user, token):
            return Response({'error': '重置链接无效或已过期'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 重置密码
        user.set_password(password)
        user.save()
        
        # 删除缓存中的令牌
        cache.delete(cache_key)
        
        logger.info(f"用户 {user.username} 密码重置成功")
        return Response({'message': '密码重置成功'})
        
    except Exception as e:
        logger.error(f"重置密码失败: {e}")
        return Response({'error': '重置密码失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)