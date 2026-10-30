from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db import transaction
from django.db.models import Q, Count
from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Role, AdminUser, Permission
from .serializers import (
    RoleSerializer, AdminUserSerializer, AdminUserCreateSerializer,
    AdminUserUpdateSerializer, PermissionSerializer, PasswordChangeSerializer
)

# 引入会员相关模型和服务
from apps.member.models import Member, MemberLevel, PointsHistory
from apps.member.serializers import MemberSerializer, MemberLevelSerializer, PointsHistorySerializer
from apps.member.services import PointsService, MemberLevelService

# 引入售后相关模型
from apps.review.models import AfterSaleRequest, AfterSaleChatMessage
from apps.review.serializers import AfterSaleRequestSerializer, AfterSaleChatMessageSerializer


class RoleViewSet(viewsets.ModelViewSet):
    """角色管理视图集"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """切换角色启用状态"""
        role = self.get_object()
        role.is_active = not role.is_active
        role.save()
        
        status_text = "启用" if role.is_active else "禁用"
        return Response({
            'message': f'角色 "{role.name}" 已{status_text}',
            'is_active': role.is_active
        })
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """获取角色下的用户列表"""
        role = self.get_object()
        users = AdminUser.objects.filter(role=role, is_active=True)
        
        # 分页
        page = self.paginate_queryset(users)
        if page is not None:
            serializer = AdminUserSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AdminUserSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """角色统计信息"""
        total_roles = Role.objects.count()
        active_roles = Role.objects.filter(is_active=True).count()
        
        return Response({
            'total_roles': total_roles,
            'active_roles': active_roles,
            'inactive_roles': total_roles - active_roles,
        })


class AdminUserViewSet(viewsets.ModelViewSet):
    """管理员用户视图集"""
    queryset = AdminUser.objects.all().select_related('role')
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'role']
    search_fields = ['username', 'real_name', 'email', 'phone']
    ordering_fields = ['username', 'created_at', 'last_login', 'login_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'create':
            return AdminUserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AdminUserUpdateSerializer
        return AdminUserSerializer
    
    def get_queryset(self):
        """优化查询并添加筛选"""
        queryset = self.queryset
        
        # 按角色筛选
        role_id = self.request.query_params.get('role_id')
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        
        # 按登录状态筛选
        has_logged_in = self.request.query_params.get('has_logged_in')
        if has_logged_in == 'true':
            queryset = queryset.filter(last_login__isnull=False)
        elif has_logged_in == 'false':
            queryset = queryset.filter(last_login__isnull=True)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """切换用户启用状态"""
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        
        status_text = "启用" if user.is_active else "禁用"
        return Response({
            'message': f'用户 "{user.username}" 已{status_text}',
            'is_active': user.is_active
        })
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """重置用户密码"""
        user = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response(
                {'error': '请提供新密码'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user.set_password(new_password)
            user.save()
            return Response({'message': f'用户 "{user.username}" 密码重置成功'})
        except DjangoValidationError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """修改密码"""
        user = self.get_object()
        serializer = PasswordChangeSerializer(
            data=request.data, 
            context={'user': user}
        )
        
        if serializer.is_valid():
            try:
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'message': '密码修改成功'})
            except DjangoValidationError as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """用户统计信息"""
        total_users = AdminUser.objects.count()
        active_users = AdminUser.objects.filter(is_active=True).count()
        users_with_role = AdminUser.objects.filter(role__isnull=False).count()
        logged_in_users = AdminUser.objects.filter(last_login__isnull=False).count()
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'users_with_role': users_with_role,
            'users_without_role': total_users - users_with_role,
            'logged_in_users': logged_in_users,
            'never_logged_in': total_users - logged_in_users,
        })


class PermissionViewSet(viewsets.ModelViewSet):
    """权限管理视图集"""
    queryset = Permission.objects.all().prefetch_related('roles')
    serializer_class = PermissionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'module']
    search_fields = ['name', 'codename', 'description']
    ordering_fields = ['name', 'module', 'created_at']
    ordering = ['module', 'name']
    
    def get_queryset(self):
        """优化查询性能"""
        return self.queryset.annotate(role_count=Count('roles'))
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """切换权限启用状态"""
        permission = self.get_object()
        permission.is_active = not permission.is_active
        permission.save()
        
        status_text = "启用" if permission.is_active else "禁用"
        return Response({
            'message': f'权限 "{permission.name}" 已{status_text}',
            'is_active': permission.is_active
        })
    
    @action(detail=True, methods=['get'])
    def roles(self, request, pk=None):
        """获取拥有该权限的角色列表"""
        permission = self.get_object()
        roles = permission.roles.filter(is_active=True)
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def modules(self, request):
        """获取所有权限模块"""
        modules = Permission.objects.values_list('module', flat=True).distinct()
        return Response(list(modules))
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """权限统计信息"""
        total_permissions = Permission.objects.count()
        active_permissions = Permission.objects.filter(is_active=True).count()
        modules_count = Permission.objects.values('module').distinct().count()
        
        return Response({
            'total_permissions': total_permissions,
            'active_permissions': active_permissions,
            'inactive_permissions': total_permissions - active_permissions,
            'modules_count': modules_count,
        })

class AdminMemberViewSet(viewsets.ModelViewSet):
    """管理员的会员管理视图集"""
    queryset = Member.objects.all().select_related('user')
    serializer_class = MemberSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = Member.objects.all().select_related('user')
        
        # 按用户名或手机号搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search) |
                Q(phone__icontains=search)
            )
        
        # 按等级过滤
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        # 按积分范围过滤
        min_points = self.request.query_params.get('min_points')
        if min_points:
            try:
                queryset = queryset.filter(points__gte=int(min_points))
            except ValueError:
                pass
        
        max_points = self.request.query_params.get('max_points')
        if max_points:
            try:
                queryset = queryset.filter(points__lte=int(max_points))
            except ValueError:
                pass
        
        return queryset.order_by('-points')
    
    @action(detail=True, methods=['post'])
    def adjust_points(self, request, pk=None):
        """调整会员积分"""
        member = self.get_object()
        points = request.data.get('points', 0)
        description = request.data.get('description', '')
        
        try:
            points = int(points)
            if not description:
                return Response(
                    {'error': '请提供调整原因'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 使用积分服务进行调整
            points_changed, level_changed, old_level, new_level = PointsService.adjust_points_by_admin(
                member, points, description, request.user.id
            )
            
            return Response({
                'success': True,
                'points_changed': points_changed,
                'level_changed': level_changed,
                'old_level': old_level,
                'new_level': new_level,
                'current_points': member.points
            })
        except ValueError:
            return Response(
                {'error': '积分必须为整数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'调整积分失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """重置会员密码"""
        member = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password or len(new_password) < 8:
            return Response(
                {'error': '新密码不能为空且长度至少为8位'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 重置密码
            user = member.user
            user.set_password(new_password)
            user.save()
            
            return Response({'message': '密码重置成功'})
        except Exception as e:
            return Response(
                {'error': f'密码重置失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def points_history(self, request, pk=None):
        """获取会员积分历史"""
        member = self.get_object()
        
        # 分页获取积分记录
        page = self.paginate_queryset(
            PointsHistory.objects.filter(member=member).order_by('-created_at')
        )
        serializer = PointsHistorySerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

class AdminMemberLevelViewSet(viewsets.ModelViewSet):
    """管理员的会员等级管理视图集"""
    queryset = MemberLevel.objects.all()
    serializer_class = MemberLevelSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = MemberLevel.objects.all()
        
        # 按激活状态过滤
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        return queryset.order_by('points_threshold')
    
    @action(detail=False, methods=['post'])
    def recompute_all_levels(self, request):
        """重新计算所有会员等级"""
        try:
            with transaction.atomic():
                # 获取所有会员
                members = Member.objects.all()
                updated_count = 0
                
                for member in members:
                    # 尝试更新会员等级
                    level_changed, old_level, new_level = member.update_level()
                    if level_changed:
                        updated_count += 1
                
                return Response({
                    'message': f'已完成所有会员等级重新计算',
                    'total_members': members.count(),
                    'updated_members': updated_count
                })
        except Exception as e:
            return Response(
                {'error': f'等级重新计算失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """获取特定等级的会员列表"""
        level = self.get_object()
        
        # 分页获取当前等级会员
        page = self.paginate_queryset(
            Member.objects.filter(level=level.name).select_related('user')
        )
        serializer = MemberSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


# 售后聊天管理功能
@api_view(['GET'])
@permission_classes([IsAdminUser])
def after_sale_chat_admin(request):
    """管理员查看售后聊天列表"""
    try:
        # 获取所有有聊天记录的售后申请
        after_sale_requests = AfterSaleRequest.objects.filter(
            chat_messages__isnull=False
        ).distinct().prefetch_related(
            'chat_messages', 'user', 'order_item__order'
        ).order_by('-updated_at')
        
        data = []
        for request in after_sale_requests:
            # 获取最新消息
            latest_message = request.chat_messages.order_by('-created_at').first()
            unread_count = request.chat_messages.filter(
                sender_type='user', 
                is_read=False
            ).count()
            
            data.append({
                'id': request.id,
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                },
                'order_item_details': {
                    'order_number': request.order_item.order.order_number,
                    'product_name': request.order_item.product_name,
                    'variant_name': request.order_item.variant_name,
                },
                'status': request.status,
                'can_chat': request.can_chat,
                'reason': request.reason,
                'handler': {
                    'id': request.handler.id,
                    'username': request.handler.username,
                    'first_name': request.handler.first_name,
                } if request.handler else None,
                'latest_message': {
                    'message': latest_message.message,
                    'sender_type': latest_message.sender_type,
                    'created_at': latest_message.created_at,
                } if latest_message else None,
                'unread_count': unread_count,
                'created_at': request.created_at,
                'updated_at': request.updated_at,
            })
        
        return Response({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def after_sale_chat_reply(request):
    """管理员回复售后聊天"""
    try:
        after_sale_request_id = request.data.get('after_sale_request_id')
        message_content = request.data.get('message', '').strip()
        
        if not after_sale_request_id or not message_content:
            return Response({
                'success': False,
                'error': '售后申请ID和消息内容不能为空'
            }, status=400)
        
        # 获取售后申请
        after_sale_request = AfterSaleRequest.objects.get(id=after_sale_request_id)
        
        # 检查是否可以聊天
        if not after_sale_request.can_chat:
            return Response({
                'success': False,
                'error': '该售后申请已完成，无法继续聊天'
            }, status=400)
        
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
        
        # 标记用户发送的消息为已读
        after_sale_request.chat_messages.filter(
            sender_type='user',
            is_read=False
        ).update(is_read=True)
        
        serializer = AfterSaleChatMessageSerializer(chat_message)
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except AfterSaleRequest.DoesNotExist:
        return Response({
            'success': False,
            'error': '售后申请不存在'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_after_sale_chat_messages(request, after_sale_id):
    """获取特定售后申请的聊天消息"""
    try:
        after_sale_request = AfterSaleRequest.objects.get(id=after_sale_id)
        messages = after_sale_request.chat_messages.all().order_by('created_at')
        
        # 标记用户发送的消息为已读
        messages.filter(sender_type='user', is_read=False).update(is_read=True)
        
        serializer = AfterSaleChatMessageSerializer(messages, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except AfterSaleRequest.DoesNotExist:
        return Response({
            'success': False,
            'error': '售后申请不存在'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def mark_after_sale_complete(request, after_sale_id):
    """标记售后申请为完成"""
    try:
        after_sale_request = AfterSaleRequest.objects.get(id=after_sale_id)
        
        after_sale_request.status = 'completed'
        after_sale_request.handler = request.user
        after_sale_request.save()
        
        return Response({
            'success': True,
            'message': '售后申请已标记为完成'
        })
        
    except AfterSaleRequest.DoesNotExist:
        return Response({
            'success': False,
            'error': '售后申请不存在'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAdminUser])  
def admin_chat_page(request):
    """管理员聊天页面"""
    from django.shortcuts import render
    return render(request, 'admin_chat.html')

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """管理员用户登录"""
    from rest_framework_simplejwt.tokens import RefreshToken
    from django.contrib.auth.models import User
    from django.contrib.auth.hashers import check_password
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        
        if not username or not password:
            return Response({
                'error': '用户名和密码不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"收到管理员登录请求: 用户名={username}")
        
        # 查找管理员用户
        try:
            admin_user = AdminUser.objects.get(username=username)
        except AdminUser.DoesNotExist:
            logger.warning(f"管理员用户不存在: {username}")
            return Response({
                'error': '用户名或密码错误'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # 检查用户是否激活
        if not admin_user.is_active:
            logger.warning(f"管理员账户已被禁用: {username}")
            return Response({
                'error': '账户已被禁用，请联系系统管理员'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # 验证密码
        if not admin_user.check_password(password):
            logger.warning(f"管理员密码错误: {username}")
            return Response({
                'error': '用户名或密码错误'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # 检查是否有对应的Django User（用于JWT认证）
        django_user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': admin_user.email or '',
                'is_staff': True,
                'is_active': True
            }
        )
        
        # 如果是新创建的用户，设置密码
        if created:
            django_user.set_password(password)
            django_user.save()
            logger.info(f"为管理员用户创建对应的Django User: {username}")
        
        # 更新管理员登录信息
        admin_user.update_login_info()
        
        # 生成JWT token
        refresh = RefreshToken.for_user(django_user)
        access_token = refresh.access_token
        
        # 准备响应数据
        response_data = {
            'message': '登录成功',
            'access': str(access_token),
            'refresh': str(refresh),
            'admin_user': {
                'id': admin_user.id,
                'username': admin_user.username,
                'real_name': admin_user.real_name,
                'email': admin_user.email,
                'phone': admin_user.phone,
                'role_name': admin_user.role_name,
                'is_active': admin_user.is_active,
                'last_login': admin_user.last_login,
                'login_count': admin_user.login_count
            }
        }
        
        logger.info(f"管理员登录成功: {username}")
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"管理员登录过程中发生错误: {e}")
        return Response({
            'error': '登录过程中发生错误，请稍后重试'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)