#!/usr/bin/env python3
"""
为用户发放新用户欢迎优惠券的管理命令
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from apps.member.models import Member, Coupon as MemberCoupon_Template, MemberCoupon


class Command(BaseCommand):
    help = '为用户发放新用户欢迎优惠券'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='指定用户ID，为特定用户发放优惠券'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='指定用户名，为特定用户发放优惠券'
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='为所有没有优惠券的用户发放优惠券'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='预览模式，不实际发放优惠券'
        )

    def handle(self, *args, **options):
        self.stdout.write('=== 新用户欢迎优惠券发放工具 ===\n')
        
        # 获取所有可用的优惠券
        available_coupons = MemberCoupon_Template.objects.filter(
            status='active',
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )
        
        total_coupons = available_coupons.count()
        if total_coupons == 0:
            self.stdout.write(self.style.WARNING('❌ 没有找到可用的优惠券！'))
            return
            
        self.stdout.write(f'📋 找到 {total_coupons} 个可用优惠券:')
        for coupon in available_coupons:
            self.stdout.write(f'  - {coupon.name} ({coupon.code}) - {coupon.get_type_display()}')
        self.stdout.write('')

        # 确定要处理的用户
        target_users = []
        
        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
                target_users = [user]
                self.stdout.write(f'🎯 目标用户: {user.username} (ID: {user.id})')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ 用户ID {options["user_id"]} 不存在'))
                return
                
        elif options['username']:
            try:
                user = User.objects.get(username=options['username'])
                target_users = [user]
                self.stdout.write(f'🎯 目标用户: {user.username} (ID: {user.id})')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ 用户名 {options["username"]} 不存在'))
                return
                
        elif options['all_users']:
            # 获取所有有Member记录但没有优惠券的用户
            users_with_members = User.objects.all()
            users_without_coupons = []
            
            for user in users_with_members:
                try:
                    # 尝试获取用户的Member记录
                    member = Member.objects.filter(user=user).first()
                    if member:
                        has_coupons = MemberCoupon.objects.filter(member=member).exists()
                        if not has_coupons:
                            users_without_coupons.append(user)
                except Exception as e:
                    self.stdout.write(f'⚠️  检查用户 {user.username} 时出错: {e}')
                    
            target_users = users_without_coupons
            self.stdout.write(f'🎯 找到 {len(target_users)} 个没有优惠券的用户')
            
        else:
            self.stdout.write(self.style.ERROR('❌ 请指定要处理的用户 (--user-id, --username, 或 --all-users)'))
            return

        if not target_users:
            self.stdout.write(self.style.WARNING('⚠️  没有找到符合条件的用户'))
            return

        # 预览模式
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('🔍 预览模式 - 不会实际发放优惠券\n'))
            
        # 处理每个用户
        success_count = 0
        total_issued = 0
        
        for user in target_users:
            try:
                # 安全地获取Member记录
                member = Member.objects.filter(user=user).first()
                if not member:
                    self.stdout.write(self.style.WARNING(f'  ⚠️  用户 {user.username} 没有Member记录'))
                    continue
                    
                self.stdout.write(f'\n👤 处理用户: {user.username} (Member ID: {member.id})')
                
                if options['dry_run']:
                    # 预览模式：只显示会发放什么优惠券
                    existing_coupons = MemberCoupon.objects.filter(member=member).values_list('coupon__code', flat=True)
                    will_issue = []
                    
                    for coupon in available_coupons:
                        if coupon.code not in existing_coupons:
                            will_issue.append(coupon)
                    
                    if will_issue:
                        self.stdout.write(f'  📦 将发放 {len(will_issue)} 个优惠券:')
                        for coupon in will_issue:
                            self.stdout.write(f'    - {coupon.name} ({coupon.code})')
                    else:
                        self.stdout.write('  ℹ️  该用户已拥有所有可用优惠券')
                else:
                    # 实际发放优惠券
                    issued_count = self.issue_coupons_to_member(member, available_coupons)
                    total_issued += issued_count
                    
                    if issued_count > 0:
                        success_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  ✅ 成功发放 {issued_count} 个优惠券'))
                    else:
                        self.stdout.write('  ℹ️  该用户已拥有所有可用优惠券')
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ 处理用户 {user.username} 时出错: {e}'))

        # 显示总结
        self.stdout.write('\n' + '='*50)
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('🔍 预览完成！'))
        else:
            self.stdout.write(self.style.SUCCESS(f'🎉 发放完成！'))
            self.stdout.write(f'📊 统计: 成功处理 {success_count}/{len(target_users)} 个用户')
            self.stdout.write(f'🎁 总共发放 {total_issued} 个优惠券')

    def issue_coupons_to_member(self, member, available_coupons):
        """为指定会员发放优惠券"""
        issued_count = 0
        
        with transaction.atomic():
            for coupon_template in available_coupons:
                # 检查是否已存在
                existing_coupon = MemberCoupon.objects.filter(
                    member=member,
                    coupon=coupon_template
                ).first()
                
                if not existing_coupon:
                    # 创建会员优惠券记录
                    MemberCoupon.objects.create(
                        member=member,
                        coupon=coupon_template,
                        status='available'
                    )
                    issued_count += 1
                    self.stdout.write(f'    ✅ {coupon_template.name} ({coupon_template.code})')
                    
        return issued_count 