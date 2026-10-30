from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Member, PointsHistory, MemberLevel

class PointsService:
    """积分处理服务类"""
    
    @staticmethod
    def add_points_for_order(member, order_id, amount):
        """
        为订单完成添加积分，1元=1积分
        
        参数:
            member: 会员对象
            order_id: 订单ID
            amount: 订单金额
        
        返回:
            (添加的积分, 是否升级, 旧等级, 新等级)
        """
        # 转换金额为整数积分，向下取整
        points_to_add = int(amount)
        if points_to_add <= 0:
            return 0, False, None, None
        
        with transaction.atomic():
            # 添加积分记录
            points_history = PointsHistory.objects.create(
                member=member,
                order_id=order_id,
                points=points_to_add,
                type='order_complete',
                description=f'订单{order_id}消费奖励积分'
            )
            
            # 更新会员积分
            member.points += points_to_add
            member.save(update_fields=['points', 'updated_at'])
            
            # 尝试升级会员等级
            level_changed, old_level, new_level = member.update_level()
            
            return points_to_add, level_changed, old_level, new_level
    
    @staticmethod
    def deduct_points_for_refund(member, order_id, amount):
        """
        为退款订单扣除积分
        
        参数:
            member: 会员对象
            order_id: 订单ID
            amount: 退款金额
        
        返回:
            (扣除的积分, 是否降级, 旧等级, 新等级)
        """
        # 查找该订单是否有对应的积分记录
        order_points_history = PointsHistory.objects.filter(
            member=member,
            order_id=order_id,
            type='order_complete'
        ).first()
        
        # 如果没有找到积分记录，不需要扣除积分
        if not order_points_history:
            return 0, False, None, None
        
        # 要扣除的积分就是之前添加的积分
        points_to_deduct = order_points_history.points
        
        with transaction.atomic():
            # 添加积分扣除记录
            PointsHistory.objects.create(
                member=member,
                order_id=order_id,
                points=-points_to_deduct,  # 负数表示扣除
                type='order_refund',
                description=f'订单{order_id}退款，扣除积分'
            )
            
            # 更新会员积分
            member.points -= points_to_deduct
            if member.points < 0:  # 防止积分为负
                member.points = 0
            member.save(update_fields=['points', 'updated_at'])
            
            # 尝试更新会员等级（可能会降级）
            level_changed, old_level, new_level = member.update_level()
            
            return points_to_deduct, level_changed, old_level, new_level
    
    @staticmethod
    def adjust_points_by_admin(member, points, description, admin_id):
        """
        管理员手动调整积分
        
        参数:
            member: 会员对象
            points: 调整积分值（正为增加，负为减少）
            description: 调整原因
            admin_id: 操作管理员ID
        
        返回:
            (调整的积分, 是否变更等级, 旧等级, 新等级)
        """
        with transaction.atomic():
            # 添加积分调整记录
            PointsHistory.objects.create(
                member=member,
                points=points,
                type='admin_adjust',
                description=description,
                admin_id=admin_id
            )
            
            # 更新会员积分
            member.points += points
            if member.points < 0:  # 防止积分为负
                member.points = 0
            member.save(update_fields=['points', 'updated_at'])
            
            # 尝试更新会员等级
            level_changed, old_level, new_level = member.update_level()
            
            return points, level_changed, old_level, new_level

class MemberLevelService:
    """会员等级服务类"""
    
    @staticmethod
    def get_member_discount(member):
        """
        获取会员折扣率
        
        参数:
            member: 会员对象
        
        返回:
            折扣率（小数）
        """
        try:
            # 获取当前会员等级
            member_level = MemberLevel.objects.filter(
                name=member.level,
                is_active=True
            ).first()
            
            # 如果找到等级信息，返回折扣率，否则返回默认值1.0（无折扣）
            return member_level.discount_rate if member_level else Decimal('1.00')
        except Exception:
            return Decimal('1.00')
    
    @staticmethod
    def get_next_level_info(member):
        """
        获取会员下一等级信息
        
        参数:
            member: 会员对象
        
        返回:
            {
                'next_level_name': 下一等级名称,
                'next_level_points': 下一等级所需积分,
                'points_needed': 还需要多少积分升级,
                'progress': 升级进度(百分比)
            }
        """
        # 获取所有等级，按积分升序排序
        levels = MemberLevel.objects.filter(is_active=True).order_by('points_threshold')
        if not levels.exists():
            return {
                'next_level_name': None,
                'next_level_points': 0,
                'points_needed': 0,
                'progress': 100
            }
        
        # 找到当前等级和下一等级
        current_level = None
        next_level = None
        
        # 找出当前会员等级对象
        for level in levels:
            if level.name == member.level:
                current_level = level
                break
        
        # 如果没找到对应等级，认为是最低级别
        if not current_level:
            current_level = levels.first()
            # 更新会员的等级为正确的等级名称
            member.level = current_level.name
            member.save(update_fields=['level'])
        
        # 找出下一等级对象
        for level in levels:
            if level.points_threshold > current_level.points_threshold:
                next_level = level
                break
        
        # 如果没找到下一等级，说明已经是最高等级
        if not next_level:
            return {
                'next_level_name': None,
                'next_level_points': 0,
                'points_needed': 0,
                'progress': 100
            }
        
        # 计算升级进度
        points_needed = next_level.points_threshold - member.points
        if points_needed < 0:
            points_needed = 0
        
        # 计算当前等级和下一等级之间的积分差距
        total_points_needed = next_level.points_threshold - current_level.points_threshold
        if total_points_needed <= 0:  # 避免除以零
            progress = 100
        else:
            # 计算从当前等级到下一等级的进度
            current_progress = member.points - current_level.points_threshold
            progress = int((current_progress / total_points_needed) * 100)
            if progress < 0:
                progress = 0
            elif progress > 100:
                progress = 100
        
        return {
            'next_level_name': next_level.name,
            'next_level_points': next_level.points_threshold,
            'points_needed': points_needed,
            'progress': progress
        } 

class MemberDiscountService:
    """会员折扣服务"""
    
    @staticmethod
    def calculate_member_discount(member, subtotal):
        """
        计算会员折扣
        
        参数:
            member: 会员对象
            subtotal: 商品小计金额
        
        返回:
            (折扣金额, 折扣率, 会员等级)
        """
        try:
            # 获取会员等级信息
            member_level = MemberLevel.objects.filter(
                name=member.level,
                is_active=True
            ).first()
            
            if not member_level:
                # 如果没有找到等级，使用默认等级（银卡会员）
                member_level = MemberLevel.objects.filter(
                    name='银卡会员',
                    is_active=True
                ).first()
                
                if not member_level:
                    # 如果连银卡会员都没有，返回无折扣
                    return Decimal('0.00'), Decimal('1.00'), member.level
            
            discount_rate = member_level.discount_rate
            
            # 计算折扣金额（原价 - 折扣后价格）
            subtotal_decimal = Decimal(str(subtotal))
            discounted_amount = subtotal_decimal * discount_rate
            discount_amount = subtotal_decimal - discounted_amount
            
            return discount_amount, discount_rate, member_level.name
            
        except Exception as e:
            print(f"计算会员折扣失败: {str(e)}")
            return Decimal('0.00'), Decimal('1.00'), member.level if member else '银卡会员'
    
    @staticmethod
    def get_member_level_info(member):
        """
        获取会员等级详情
        
        参数:
            member: 会员对象
        
        返回:
            会员等级信息字典
        """
        try:
            member_level = MemberLevel.objects.filter(
                name=member.level,
                is_active=True
            ).first()
            
            if not member_level:
                member_level = MemberLevel.objects.filter(
                    name='银卡会员',
                    is_active=True
                ).first()
            
            if member_level:
                return {
                    'name': member_level.name,
                    'discount_rate': float(member_level.discount_rate),
                    'discount_percentage': int((1 - member_level.discount_rate) * 100),
                    'points_threshold': member_level.points_threshold,
                    'description': member_level.description,
                    'icon': member_level.icon
                }
            else:
                return {
                    'name': '银卡会员',
                    'discount_rate': 1.00,
                    'discount_percentage': 0,
                    'points_threshold': 0,
                    'description': '初始会员，享受基本服务',
                    'icon': '/images/silver_icon.png'
                }
                
        except Exception as e:
            print(f"获取会员等级信息失败: {str(e)}")
            return {
                'name': '银卡会员',
                'discount_rate': 1.00,
                'discount_percentage': 0,
                'points_threshold': 0,
                'description': '初始会员，享受基本服务',
                'icon': '/images/silver_icon.png'
            } 