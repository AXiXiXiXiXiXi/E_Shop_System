from django.db import migrations
from decimal import Decimal

def add_member_levels(apps, schema_editor):
    """添加默认会员等级"""
    MemberLevel = apps.get_model('member', 'MemberLevel')
    
    # 创建会员等级
    levels = [
        {
            'name': '银卡会员',
            'points_threshold': 0,
            'discount_rate': Decimal('1.00'),
            'icon': '/images/silver_icon.png',
            'description': '初始会员等级，享受基本服务'
        },
        {
            'name': '金卡会员',
            'points_threshold': 5000,
            'discount_rate': Decimal('0.95'),
            'icon': '/images/gold_icon.png',
            'description': '中级会员，享受95折优惠'
        },
        {
            'name': '钻石会员',
            'points_threshold': 10000,
            'discount_rate': Decimal('0.90'),
            'icon': '/images/diamond_icon.png',
            'description': '高级会员，享受9折优惠和专属客服'
        },
        {
            'name': '黑钻会员',
            'points_threshold': 20000,
            'discount_rate': Decimal('0.85'),
            'icon': '/images/black_diamond_icon.png',
            'description': '尊贵会员，享受8.5折优惠和全场免运费'
        }
    ]
    
    # 清除现有等级
    MemberLevel.objects.all().delete()
    
    # 添加新等级
    for level_data in levels:
        MemberLevel.objects.create(**level_data)

def remove_member_levels(apps, schema_editor):
    """删除默认会员等级"""
    MemberLevel = apps.get_model('member', 'MemberLevel')
    MemberLevel.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('member', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(add_member_levels, remove_member_levels),
    ] 