from rest_framework import viewsets, status, permissions, serializers, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.db.models import F
from django.contrib.auth.models import User
from .models import (
    Member, Address, MemberLevel, PointsHistory,
    Coupon, MemberCoupon, RechargeRecord
)
from .serializers import (
    MemberSerializer, MemberDetailSerializer, AddressSerializer,
    MemberLevelSerializer, PointsHistorySerializer, RechargeRecordSerializer
)
from .services import PointsService, MemberLevelService

class MemberViewSet(viewsets.ModelViewSet):
    """会员视图集"""
    queryset = Member.objects.select_related('user')
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MemberDetailSerializer
        return MemberSerializer
    
    def get_queryset(self):
        # 用户只能查看自己的会员信息
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def current_member(self, request):
        """获取当前登录用户的会员信息"""
        try:
            # 先尝试获取当前用户的Member记录
            member = Member.objects.select_related('user').get(user=request.user)
            serializer = self.get_serializer(member)
            
            # 获取会员等级信息
            level_info = MemberLevelService.get_next_level_info(member)
            
            # 合并会员信息和等级信息
            data = serializer.data
            data.update({
                'next_level_name': level_info['next_level_name'],
                'next_level_points': level_info['next_level_points'],
                'points_needed': level_info['points_needed'],
                'progress': level_info['progress'],
                'current_level_points': member.points
            })
            
            return Response(data)
        except Member.DoesNotExist:
            # 如果记录不存在，返回404
            return Response(
                {'error': '会员信息不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def points_history(self, request, pk=None):
        """获取会员积分历史记录"""
        member = self.get_object()
        
        # 分页获取积分记录
        page = self.paginate_queryset(
            PointsHistory.objects.filter(member=member).order_by('-created_at')
        )
        serializer = PointsHistorySerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def next_level(self, request, pk=None):
        """获取会员下一等级信息"""
        member = self.get_object()
        level_info = MemberLevelService.get_next_level_info(member)
        
        return Response(level_info)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def adjust_points(self, request, pk=None):
        """管理员调整会员积分"""
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

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def discount_info(self, request):
        """
        获取当前用户的会员折扣信息
        """
        try:
            member = Member.objects.get(user=request.user)
            from apps.member.services import MemberDiscountService
            
            # 获取会员等级信息
            level_info = MemberDiscountService.get_member_level_info(member)
            
            return Response({
                'member_level': level_info['name'],
                'discount_rate': level_info['discount_rate'],
                'discount_percentage': level_info['discount_percentage'],
                'points': member.points,
                'points_threshold': level_info['points_threshold'],
                'description': level_info['description'],
                'icon': level_info['icon']
            })
            
        except Member.DoesNotExist:
            return Response(
                {'error': '会员信息不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'获取折扣信息失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def recharge(self, request):
        """
        会员余额充值API
        """
        try:
            print(f"收到充值请求: {request.data}")
            amount = float(request.data.get('amount', 0))
            if amount <= 0:
                return Response({'detail': '充值金额必须大于0'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 获取当前会员
            try:
                member = Member.objects.get(user=request.user)
            except Member.DoesNotExist:
                print(f"会员不存在，用户ID: {request.user.id}")
                return Response({'detail': '会员信息不存在'}, status=status.HTTP_404_NOT_FOUND)
            
            print(f"找到会员: {member.id}, 当前余额: {member.balance}")
            
            # 更新余额并创建充值记录
            try:
                with transaction.atomic():
                    # 创建充值记录
                    recharge_record = RechargeRecord(
                        member=member,
                        amount=amount,
                        status='success',
                        payment_method='online',
                        remark='会员中心在线充值'
                    )
                    recharge_record.save()
                    print(f"创建充值记录成功: {recharge_record.id}")
                    
                    # 更新会员余额
                    old_balance = member.balance
                    member.balance = float(old_balance) + amount
                    member.save()
                    print(f"更新会员余额成功: {old_balance} -> {member.balance}")
                    
                    # 重新获取会员信息以返回最新余额
                    member.refresh_from_db()
                
                print(f"充值成功，新余额: {member.balance}")
                return Response({
                    'success': True,
                    'message': '充值成功',
                    'new_balance': member.balance,
                    'recharge_id': recharge_record.id
                }, status=status.HTTP_200_OK)
            except Exception as e:
                print(f"充值事务处理失败: {str(e)}")
                return Response({'detail': f'充值处理失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError:
            print("无效的充值金额")
            return Response({'detail': '无效的充值金额'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"充值过程中发生未知错误: {str(e)}")
            return Response({'detail': f'充值失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddressViewSet(viewsets.ModelViewSet):
    """收货地址视图集"""
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """只返回当前用户的地址"""
        try:
            # 尝试获取用户关联的会员
            member = Member.objects.get(user=self.request.user)
            # 使用SQL原生查询格式，确保返回所有字段
            addresses = Address.objects.filter(member=member).order_by('-is_default', '-updated_at')
            print(f"查询到{addresses.count()}个地址记录")
            return addresses
        except Member.DoesNotExist:
            print("未找到会员记录")
            return Address.objects.none()
    
    def list(self, request, *args, **kwargs):
        """重写列表方法，确保返回的是数组格式"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        print(f"序列化地址数据: {serializer.data}")
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """创建地址时自动关联到当前用户"""
        try:
            member = Member.objects.get(user=self.request.user)
            # 如果设置为默认地址，则将其他地址设为非默认
            is_default = serializer.validated_data.get('is_default', False)
            if is_default:
                Address.objects.filter(member=member, is_default=True).update(is_default=False)
            
            # 保存地址
            serializer.save(member=member)
            print(f"已为会员 {member.id} 创建新地址")
        except Member.DoesNotExist:
            raise serializers.ValidationError("用户会员信息不存在")
    
    def update(self, request, *args, **kwargs):
        """更新地址信息"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # 如果设置为默认地址，则将其他地址设为非默认
        if request.data.get('is_default', False):
            Address.objects.filter(member=instance.member, is_default=True).exclude(id=instance.id).update(is_default=False)
        
        self.perform_update(serializer)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """设置默认地址"""
        try:
            member = Member.objects.get(user=request.user)
            address = self.get_object()
            
            # 确保地址属于当前用户
            if address.member != member:
                return Response(
                    {'error': '无权操作此地址'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 将其他地址设为非默认
            Address.objects.filter(member=member, is_default=True).update(is_default=False)
            
            # 设置当前地址为默认
            address.is_default = True
            address.save()
            
            return Response({'message': '已设为默认地址'})
        except Member.DoesNotExist:
            return Response(
                {'error': '会员信息不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Address.DoesNotExist:
            return Response(
                {'error': '地址不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

class MemberLevelViewSet(viewsets.ModelViewSet):
    """会员等级视图集"""
    queryset = MemberLevel.objects.all()
    serializer_class = MemberLevelSerializer
    permission_classes = [permissions.IsAdminUser]  # 仅管理员可以管理会员等级
    
    def get_queryset(self):
        # 允许根据活跃状态过滤
        queryset = MemberLevel.objects.all()
        is_active = self.request.query_params.get('is_active')
        
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        return queryset.order_by('points_threshold')
    
    @action(detail=False, methods=['get'])
    def public(self, request):
        """获取所有公开可见的会员等级信息（非管理员可访问）"""
        queryset = MemberLevel.objects.filter(is_active=True).order_by('points_threshold')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class PointsHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """积分历史记录视图集（仅查看）"""
    serializer_class = PointsHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            # 管理员可以查看所有记录
            return PointsHistory.objects.all().order_by('-created_at')
        else:
            # 普通用户只能查看自己的记录
            try:
                member = Member.objects.get(user=self.request.user)
                return PointsHistory.objects.filter(member=member).order_by('-created_at')
            except Member.DoesNotExist:
                return PointsHistory.objects.none()
