from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.member.models import Member, MemberLevel
from apps.member.services import MemberDiscountService
from decimal import Decimal


class Command(BaseCommand):
    help = 'Test member discount functionality'

    def handle(self, *args, **options):
        self.stdout.write("开始测试会员折扣功能...")
        
        # 检查会员等级设置
        levels = MemberLevel.objects.filter(is_active=True).order_by('points_threshold')
        self.stdout.write(f"\n📋 当前会员等级设置:")
        for level in levels:
            discount_percentage = int((1 - level.discount_rate) * 100)
            self.stdout.write(f"   {level.name}: {level.points_threshold} 积分, 折扣率: {level.discount_rate}, 优惠: {discount_percentage}%")
        
        # 查找测试用户
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("❌ 没有找到测试用户"))
            return
        
        self.stdout.write(f"\n✅ 找到测试用户: {user.username}")
        
        # 获取或创建会员资料
        member, created = Member.objects.get_or_create(
            user=user,
            defaults={
                'points': 0,
                'level': '银卡会员',
                'total_orders': 0,
                'total_spent': Decimal('0.00')
            }
        )
        
        if created:
            self.stdout.write(f"✅ 创建了会员资料: {member}")
        else:
            self.stdout.write(f"✅ 找到会员资料: {member}")
        
        # 测试不同积分等级下的折扣计算
        test_amounts = [100, 500, 1000, 2000]
        test_points = [0, 3000, 8000, 15000, 25000]
        
        self.stdout.write(f"\n🧪 测试会员折扣计算:")
        
        for points in test_points:
            # 更新会员积分
            member.points = points
            member.save()
            
            # 更新会员等级
            level_changed, old_level, new_level = member.update_level()
            if level_changed:
                self.stdout.write(f"   等级更新: {old_level} → {new_level}")
            
            # 获取会员等级信息
            level_info = MemberDiscountService.get_member_level_info(member)
            
            self.stdout.write(f"\n📊 积分: {points}, 等级: {level_info['name']}")
            self.stdout.write(f"   折扣率: {level_info['discount_rate']}, 优惠: {level_info['discount_percentage']}%")
            
            # 测试不同金额的折扣计算
            for amount in test_amounts:
                discount_amount, discount_rate, member_level = MemberDiscountService.calculate_member_discount(
                    member, amount
                )
                
                final_price = amount - discount_amount
                
                self.stdout.write(f"   订单 ¥{amount}: 折扣 ¥{discount_amount:.2f}, 实付 ¥{final_price:.2f}")
        
        # 测试API接口
        self.stdout.write(f"\n🌐 测试折扣信息API:")
        
        # 模拟API调用
        try:
            level_info = MemberDiscountService.get_member_level_info(member)
            self.stdout.write(f"✅ API响应示例:")
            self.stdout.write(f"   member_level: {level_info['name']}")
            self.stdout.write(f"   discount_rate: {level_info['discount_rate']}")
            self.stdout.write(f"   discount_percentage: {level_info['discount_percentage']}")
            self.stdout.write(f"   points: {member.points}")
            self.stdout.write(f"   points_threshold: {level_info['points_threshold']}")
            self.stdout.write(f"   description: {level_info['description']}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ API测试失败: {str(e)}"))
        
        # 实际折扣计算示例
        self.stdout.write(f"\n💰 实际购物场景测试:")
        scenarios = [
            {"subtotal": 299, "description": "小额购物"},
            {"subtotal": 1299, "description": "中等消费"},
            {"subtotal": 3999, "description": "大额购买"},
        ]
        
        for scenario in scenarios:
            subtotal = scenario["subtotal"]
            description = scenario["description"]
            
            discount_amount, discount_rate, member_level = MemberDiscountService.calculate_member_discount(
                member, subtotal
            )
            
            final_price = subtotal - discount_amount
            
            self.stdout.write(f"   {description} (¥{subtotal}):")
            self.stdout.write(f"     会员等级: {member_level}")
            self.stdout.write(f"     折扣金额: ¥{discount_amount:.2f}")
            self.stdout.write(f"     实际支付: ¥{final_price:.2f}")
            
            if discount_amount > 0:
                savings_percentage = (discount_amount / subtotal) * 100
                self.stdout.write(f"     节省: {savings_percentage:.1f}%")
        
        self.stdout.write(f"\n✅ 会员折扣功能测试完成") 