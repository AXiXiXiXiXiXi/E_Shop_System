from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import connection
from django.utils import timezone

@receiver(post_save, sender=User)
def create_member_for_new_user(sender, instance, created, **kwargs):
    """
    当创建新用户时，自动创建对应的会员记录并发放所有可用优惠券
    """
    print(f"信号被触发: user={instance.username}, created={created}")
    
    if created:  # 只在用户首次创建时触发
        print(f"开始为新用户 {instance.username} 创建Member记录和发放优惠券...")
        
        # 获取phone字段（如果存在）
        phone = ''
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT phone FROM auth_user WHERE id = %s", [instance.id])
                result = cursor.fetchone()
                if result and result[0]:
                    phone = result[0]
        except Exception as e:
            print(f"获取用户phone字段失败: {e}")
            phone = '00000000000'  # 默认值

        # 创建Member记录
        member_id = None
        try:
            # 检查是否已存在Member记录
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM member_member WHERE user_id = %s", [instance.id])
                existing_member = cursor.fetchone()
                
                if not existing_member:
                    # 准备时间戳
                    now = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 插入记录
                    cursor.execute("""
                        INSERT INTO member_member 
                        (user_id, phone, level, points, growth_value, balance, total_orders, total_spent, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [
                        instance.id,  # user_id
                        phone,        # phone
                        'normal',     # level (字符串，而不是level_id)
                        0,            # points
                        0,            # growth_value
                        0.00,         # balance
                        0,            # total_orders
                        0.00,         # total_spent
                        now,          # created_at
                        now           # updated_at
                    ])
                    
                    # 获取新创建的member ID
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    member_id = cursor.fetchone()[0]
                    print(f"已为用户 {instance.username} (ID: {instance.id}) 创建会员记录 (Member ID: {member_id})")
                else:
                    member_id = existing_member[0]
                    print(f"用户 {instance.username} 的会员记录已存在 (Member ID: {member_id})")
                    
        except Exception as e:
            print(f"创建会员记录失败: {e}")
            
        # 如果成功创建或找到了Member记录，发放所有可用优惠券
        if member_id:
            try:
                print(f"准备为Member ID {member_id} 发放优惠券...")
                auto_issue_all_coupons_to_new_member(member_id, instance.username)
            except Exception as e:
                print(f"为新用户 {instance.username} 发放优惠券失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"无法为用户 {instance.username} 发放优惠券，因为member_id为空")

def auto_issue_all_coupons_to_new_member(member_id, username):
    """
    为新注册用户自动发放所有可用的优惠券
    """
    from apps.member.models import Coupon as MemberCoupon_Template, MemberCoupon
    
    print(f"开始为新用户 {username} (Member ID: {member_id}) 发放优惠券...")
    
    # 获取所有可用的优惠券模板
    available_coupons = MemberCoupon_Template.objects.filter(
        status='active',
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    )
    
    issued_count = 0
    total_coupons = available_coupons.count()
    
    print(f"找到 {total_coupons} 个可用优惠券")
    
    # 为每个可用优惠券创建会员优惠券记录
    for coupon_template in available_coupons:
        try:
            # 检查用户是否已经拥有该优惠券
            existing_coupon = MemberCoupon.objects.filter(
                member_id=member_id,
                coupon=coupon_template
            ).first()
            
            if not existing_coupon:
                # 创建会员优惠券记录
                MemberCoupon.objects.create(
                    member_id=member_id,
                    coupon=coupon_template,
                    status='available'
                )
                issued_count += 1
                print(f"  ✅ 发放优惠券: {coupon_template.name} ({coupon_template.code})")
            else:
                print(f"  ⚠️  优惠券已存在: {coupon_template.name} ({coupon_template.code})")
                
        except Exception as e:
            print(f"  ❌ 发放优惠券失败 {coupon_template.name}: {e}")
    
    print(f"优惠券发放完成！成功发放 {issued_count}/{total_coupons} 个优惠券给用户 {username}")
    
    # 记录优惠券发放日志
    try:
        with connection.cursor() as cursor:
            log_message = f"新用户注册自动发放优惠券: 成功 {issued_count}/{total_coupons}"
            cursor.execute("""
                INSERT INTO member_pointshistory 
                (member_id, change_type, change_amount, reason, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, [
                member_id,
                'register_bonus',
                0,  # 优惠券不是积分，所以积分变化为0
                log_message,
                timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
            print(f"已记录优惠券发放日志")
    except Exception as e:
        print(f"记录优惠券发放日志失败: {e}") 