from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.member.models import Member, PointsHistory
from apps.member.services import PointsService
from apps.order.models import Order
from decimal import Decimal


class Command(BaseCommand):
    help = 'Test points system'

    def handle(self, *args, **options):
        self.stdout.write("开始测试积分系统...")
        
        # 查找一个测试用户
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("❌ 没有找到测试用户"))
            return
        
        self.stdout.write(f"✅ 找到测试用户: {user.username}")
        
        # 获取或创建会员资料
        member, created = Member.objects.get_or_create(
            user=user,
            defaults={
                'points': 0,
                'level': 'bronze',
                'total_orders': 0,
                'total_spent': Decimal('0.00')
            }
        )
        
        if created:
            self.stdout.write(f"✅ 创建了会员资料: {member}")
        else:
            self.stdout.write(f"✅ 找到会员资料: {member}")
        
        self.stdout.write(f"📊 当前积分: {member.points}")
        self.stdout.write(f"📊 当前等级: {member.level}")
        
        # 测试积分服务
        test_order_id = 999999
        test_amount = Decimal('100.50')
        
        self.stdout.write(f"\n🧪 测试积分服务...")
        self.stdout.write(f"   订单ID: {test_order_id}")
        self.stdout.write(f"   订单金额: {test_amount}")
        
        try:
            # 添加积分
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
            self.stdout.write(self.style.ERROR(f"❌ 积分服务测试失败: {str(e)}"))
        
        # 刷新会员信息
        member.refresh_from_db()
        self.stdout.write(f"📊 更新后积分: {member.points}")
        
        # 查看所有已完成订单
        completed_orders = Order.objects.filter(user=user, status='completed')
        self.stdout.write(f"\n🔍 用户的已完成订单数量: {completed_orders.count()}")
        
        for order in completed_orders[:3]:  # 只看前3个
            self.stdout.write(f"   订单: {order.order_number}, 金额: {order.total_price}")
            
            # 检查积分记录
            points_record = PointsHistory.objects.filter(
                member=member,
                order_id=order.id,
                type='order_complete'
            ).first()
            
            if points_record:
                self.stdout.write(f"     ✅ 已有积分记录: {points_record.points} 积分")
            else:
                self.stdout.write(f"     ❌ 缺少积分记录")
        
        # 列出所有积分历史
        self.stdout.write(f"\n📋 最近积分历史记录:")
        all_points_history = PointsHistory.objects.filter(member=member).order_by('-created_at')[:5]
        
        if all_points_history:
            for history in all_points_history:
                self.stdout.write(f"   {history.created_at.strftime('%Y-%m-%d %H:%M')} | "
                                  f"{history.get_type_display()} | "
                                  f"{history.points:+d} 积分 | "
                                  f"订单: {history.order_id or 'N/A'}")
        else:
            self.stdout.write("   无积分历史记录")
        
        self.stdout.write(f"\n✅ 积分系统测试完成") 