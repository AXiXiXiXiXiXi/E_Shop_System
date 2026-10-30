from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.member.models import Member, PointsHistory, MemberLevel
from apps.member.services import PointsService
from decimal import Decimal


class Command(BaseCommand):
    help = 'Test member level downgrade on refund'

    def handle(self, *args, **options):
        self.stdout.write("开始测试会员等级降级...")
        
        # 查找一个测试用户
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("❌ 没有找到测试用户"))
            return
        
        self.stdout.write(f"✅ 找到测试用户: {user.username}")
        
        # 检查会员等级设置
        levels = MemberLevel.objects.filter(is_active=True).order_by('points_threshold')
        self.stdout.write(f"\n📋 当前会员等级设置:")
        for level in levels:
            self.stdout.write(f"   {level.name}: {level.points_threshold} 积分")
        
        # 获取或创建会员资料，设置一个较高的积分（确保在某个等级）
        member, created = Member.objects.get_or_create(
            user=user,
            defaults={
                'points': 1500,  # 设置较高积分
                'level': 'bronze',
                'total_orders': 0,
                'total_spent': Decimal('0.00')
            }
        )
        
        # 更新积分到1500
        member.points = 1500
        member.save()
        
        # 更新等级
        level_changed, old_level, new_level = member.update_level()
        if level_changed:
            self.stdout.write(f"✅ 等级已更新: {old_level} → {new_level}")
        
        self.stdout.write(f"📊 测试前积分: {member.points}")
        self.stdout.write(f"📊 测试前等级: {member.level}")
        
        # 模拟一个大订单完成，增加更多积分
        test_order_id = 777777
        test_amount = Decimal('1000.00')  # 大订单
        
        self.stdout.write(f"\n🧪 第一步：模拟大订单完成...")
        self.stdout.write(f"   订单ID: {test_order_id}")
        self.stdout.write(f"   订单金额: {test_amount}")
        
        try:
            # 先添加积分（模拟订单完成）
            points_added, level_changed, old_level, new_level = PointsService.add_points_for_order(
                member=member,
                order_id=test_order_id,
                amount=test_amount
            )
            
            self.stdout.write(f"✅ 积分添加结果:")
            self.stdout.write(f"   添加积分: {points_added}")
            self.stdout.write(f"   等级变化: {level_changed}")
            
            if level_changed:
                self.stdout.write(f"   旧等级: {old_level}")
                self.stdout.write(f"   新等级: {new_level}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ 积分添加失败: {str(e)}"))
            return
        
        # 刷新会员信息
        member.refresh_from_db()
        self.stdout.write(f"📊 增加积分后: {member.points}")
        self.stdout.write(f"📊 增加积分后等级: {member.level}")
        
        # 现在测试退款积分扣除和降级
        self.stdout.write(f"\n🧪 第二步：模拟退款，测试降级...")
        
        try:
            # 扣除积分（模拟退款）
            points_deducted, level_changed, old_level, new_level = PointsService.deduct_points_for_refund(
                member=member,
                order_id=test_order_id,
                amount=test_amount
            )
            
            self.stdout.write(f"✅ 积分扣除结果:")
            self.stdout.write(f"   扣除积分: {points_deducted}")
            self.stdout.write(f"   等级变化: {level_changed}")
            
            if level_changed:
                self.stdout.write(self.style.SUCCESS(f"   🔽 等级降级: {old_level} → {new_level}"))
            else:
                self.stdout.write(f"   等级保持: {member.level}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ 积分扣除失败: {str(e)}"))
        
        # 刷新会员信息
        member.refresh_from_db()
        self.stdout.write(f"📊 扣除积分后: {member.points}")
        self.stdout.write(f"📊 扣除积分后等级: {member.level}")
        
        # 检查积分历史记录
        self.stdout.write(f"\n📋 该订单的积分历史记录:")
        history_records = PointsHistory.objects.filter(
            member=member, 
            order_id=test_order_id
        ).order_by('created_at')
        
        for history in history_records:
            action = "获得" if history.points > 0 else "扣除"
            self.stdout.write(f"   {history.created_at.strftime('%Y-%m-%d %H:%M')} | "
                              f"{history.get_type_display()} | "
                              f"{action} {abs(history.points)} 积分 | "
                              f"{history.description}")
        
        self.stdout.write(f"\n✅ 会员等级降级测试完成") 