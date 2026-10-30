from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from .models import PasswordResetRequest
from .serializers import PasswordResetRequestSerializer, PasswordResetRequestListSerializer
import logging

logger = logging.getLogger(__name__)

def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_password_reset_request(request):
    """提交密码重置请求"""
    try:
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            # 保存请求
            reset_request = serializer.save(
                client_ip=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            logger.info(f"收到密码重置请求 - ID: {reset_request.id}, 用户名: {reset_request.username}")
            
            return Response({
                'message': '密码重置请求已提交，管理员将尽快处理您的申请',
                'request_id': reset_request.id,
                'status': '您的请求已进入审核队列，请耐心等待处理结果'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': '提交失败，请检查您的信息',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"提交密码重置请求失败: {e}")
        return Response({
            'error': '提交失败，请稍后重试'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_password_reset_requests(request):
    """管理员查看所有密码重置请求"""
    try:
        status_filter = request.GET.get('status', '')
        queryset = PasswordResetRequest.objects.all()
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 分页
        page_size = int(request.GET.get('page_size', 20))
        page = int(request.GET.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = queryset.count()
        requests = queryset[start:end]
        
        serializer = PasswordResetRequestListSerializer(requests, many=True)
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })
        
    except Exception as e:
        logger.error(f"获取密码重置请求列表失败: {e}")
        return Response({
            'error': '获取数据失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_password_reset_request(request, request_id):
    """管理员批准密码重置请求"""
    try:
        reset_request = PasswordResetRequest.objects.get(id=request_id)
        
        if reset_request.status != 'pending':
            return Response({
                'error': f'请求状态为 {reset_request.get_status_display()}，无法处理'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success, message = reset_request.approve_and_reset_password(request.user)
        
        if success:
            logger.info(f"管理员 {request.user.username} 批准了密码重置请求 {request_id}")
            return Response({
                'message': message,
                'status': 'completed'
            })
        else:
            return Response({
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except PasswordResetRequest.DoesNotExist:
        return Response({
            'error': '请求不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"批准密码重置请求失败: {e}")
        return Response({
            'error': '处理失败，请稍后重试'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def reject_password_reset_request(request, request_id):
    """管理员拒绝密码重置请求"""
    try:
        reset_request = PasswordResetRequest.objects.get(id=request_id)
        
        if reset_request.status != 'pending':
            return Response({
                'error': f'请求状态为 {reset_request.get_status_display()}，无法处理'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        admin_notes = request.data.get('admin_notes', '管理员拒绝了此请求')
        
        reset_request.status = 'rejected'
        reset_request.processed_by = request.user
        reset_request.processed_at = timezone.now()
        reset_request.admin_notes = admin_notes
        reset_request.save()
        
        logger.info(f"管理员 {request.user.username} 拒绝了密码重置请求 {request_id}")
        
        return Response({
            'message': '请求已拒绝',
            'status': 'rejected'
        })
        
    except PasswordResetRequest.DoesNotExist:
        return Response({
            'error': '请求不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"拒绝密码重置请求失败: {e}")
        return Response({
            'error': '处理失败，请稍后重试'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_password_reset_request_detail(request, request_id):
    """获取密码重置请求详情"""
    try:
        reset_request = PasswordResetRequest.objects.get(id=request_id)
        serializer = PasswordResetRequestListSerializer(reset_request)
        
        # 添加匹配用户信息
        data = serializer.data
        if reset_request.find_matching_user():
            user = reset_request.find_matching_user()
            data['matching_user_info'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'date_joined': user.date_joined,
                'is_active': user.is_active
            }
        
        return Response(data)
        
    except PasswordResetRequest.DoesNotExist:
        return Response({
            'error': '请求不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"获取密码重置请求详情失败: {e}")
        return Response({
            'error': '获取数据失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
