from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.member.models import Member, PointsHistory
from apps.member.services import PointsService
from apps.order.models import Order
from decimal import Decimal


class Command(BaseCommand):
    help = 'Test refund points deduction system'

    def handle(self, *args, **options):
        self.stdout.write("开始测试退款积分扣除系统...")
        
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
                'points': 100,  # 设置一些初始积分
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
        
        # 查找一个真实的订单来测试
        test_order = Order.objects.filter(user=user).first()
        if not test_order:
            self.stdout.write(self.style.WARNING("⚠️  没有找到测试订单，创建一个虚拟测试"))
            test_order_id = 1  # 使用一个简单的ID
        else:
            test_order_id = test_order.id
            self.stdout.write(f"✅ 找到测试订单: {test_order.order_number}")
        
        test_amount = Decimal('200.00')
        
        self.stdout.write(f"\n🧪 第一步：模拟订单完成，增加积分...")
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
        
        # 现在测试退款积分扣除
        self.stdout.write(f"\n🧪 第二步：模拟退款，扣除积分...")
        
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
                self.stdout.write(f"   旧等级: {old_level}")
                self.stdout.write(f"   新等级: {new_level}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ 积分扣除失败: {str(e)}"))
        
        # 刷新会员信息
        member.refresh_from_db()
        self.stdout.write(f"📊 扣除积分后: {member.points}")
        self.stdout.write(f"📊 扣除积分后等级: {member.level}")
        
        # 检查积分历史记录
        self.stdout.write(f"\n📋 积分历史记录:")
        all_points_history = PointsHistory.objects.filter(
            member=member, 
            order_id=test_order_id
        ).order_by('-created_at')
        
        if all_points_history:
            for history in all_points_history:
                action = "获得" if history.points > 0 else "扣除"
                self.stdout.write(f"   {history.created_at.strftime('%Y-%m-%d %H:%M')} | "
                                  f"{history.get_type_display()} | "
                                  f"{action} {abs(history.points)} 积分 | "
                                  f"{history.description}")
        else:
            self.stdout.write("   无相关积分历史记录")
        
        # 查看真实订单
        self.stdout.write(f"\n🔍 查找用户的真实已完成订单...")
        completed_orders = Order.objects.filter(user=user, status='completed')
        self.stdout.write(f"   已完成订单数量: {completed_orders.count()}")
        
        for order in completed_orders[:2]:  # 只看前2个
            self.stdout.write(f"   订单: {order.order_number}, 金额: {order.total_price}")
            
            # 检查积分记录
            points_record = PointsHistory.objects.filter(
                member=member,
                order_id=order.id,
                type='order_complete'
            ).first()
            
            if points_record:
                self.stdout.write(f"     ✅ 有积分获得记录: {points_record.points} 积分")
                
                # 检查是否有退款记录
                refund_record = PointsHistory.objects.filter(
                    member=member,
                    order_id=order.id,
                    type='order_refund'
                ).first()
                
                if refund_record:
                    self.stdout.write(f"     🔄 有积分扣除记录: {abs(refund_record.points)} 积分")
                else:
                    self.stdout.write(f"     ℹ️  无积分扣除记录")
            else:
                self.stdout.write(f"     ❌ 缺少积分获得记录")
        
        self.stdout.write(f"\n✅ 退款积分扣除系统测试完成") 