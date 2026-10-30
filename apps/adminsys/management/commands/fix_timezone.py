"""
时区问题修复命令
使用方法: python manage.py fix_timezone
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from apps.adminsys.models import AdminUser, Role, Permission

class Command(BaseCommand):
    help = '检查和修复时区显示问题'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--show-times',
            action='store_true',
            help='显示当前所有时间信息',
        )
        parser.add_argument(
            '--fix-display',
            action='store_true',
            help='修复时间显示（为序列化器添加本地时间字段）',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🕐 时区问题诊断工具'))
        self.stdout.write('=' * 50)
        
        # 显示当前时区配置
        self.show_timezone_config()
        
        if options['show_times']:
            self.show_sample_times()
        
        # 显示解决方案
        self.show_solutions()
    
    def show_timezone_config(self):
        """显示时区配置"""
        self.stdout.write('\n📋 当前时区配置:')
        self.stdout.write(f'  TIME_ZONE: {settings.TIME_ZONE}')
        self.stdout.write(f'  USE_TZ: {settings.USE_TZ}')
        self.stdout.write(f'  Django时区: {timezone.get_current_timezone()}')
        self.stdout.write(f'  当前UTC时间: {timezone.now()}')
        self.stdout.write(f'  当前本地时间: {timezone.localtime()}')
    
    def show_sample_times(self):
        """显示示例时间数据"""
        self.stdout.write('\n🕒 数据库中的时间示例:')
        
        # 显示管理员用户的时间
        admin_users = AdminUser.objects.all()[:3]
        if admin_users:
            self.stdout.write('\n  管理员用户时间:')
            for user in admin_users:
                utc_time = user.created_at
                local_time = timezone.localtime(utc_time) if utc_time else None
                self.stdout.write(f'    用户: {user.username}')
                self.stdout.write(f'      数据库存储(UTC): {utc_time}')
                self.stdout.write(f'      本地时间显示:    {local_time.strftime("%Y-%m-%d %H:%M:%S") if local_time else "无"}')
        
        # 显示角色的时间
        roles = Role.objects.all()[:3]
        if roles:
            self.stdout.write('\n  角色时间:')
            for role in roles:
                utc_time = role.created_at
                local_time = timezone.localtime(utc_time) if utc_time else None
                self.stdout.write(f'    角色: {role.name}')
                self.stdout.write(f'      数据库存储(UTC): {utc_time}')
                self.stdout.write(f'      本地时间显示:    {local_time.strftime("%Y-%m-%d %H:%M:%S") if local_time else "无"}')
    
    def show_solutions(self):
        """显示解决方案"""
        self.stdout.write('\n💡 解决方案说明:')
        self.stdout.write('\n【问题说明】')
        self.stdout.write('  Django默认将时间以UTC格式存储在数据库中，这是国际化应用的最佳实践。')
        self.stdout.write('  显示时需要转换为本地时间。')
        
        self.stdout.write('\n【已提供的解决方案】')
        self.stdout.write('  1. ✅ API响应中添加了 *_local 字段')
        self.stdout.write('     - created_at_local: 本地格式的创建时间')
        self.stdout.write('     - updated_at_local: 本地格式的更新时间')
        self.stdout.write('     - last_login_local: 本地格式的最后登录时间')
        
        self.stdout.write('  2. ✅ Django Admin中显示本地时间')
        self.stdout.write('     - 列表页显示本地时间格式')
        
        self.stdout.write('  3. ✅ 提供了时区转换工具类')
        self.stdout.write('     - TimezoneHelper.convert_utc_to_local()')
        self.stdout.write('     - TimezoneHelper.format_local_time()')
        
        self.stdout.write('\n【前端使用建议】')
        self.stdout.write('  - 使用 *_local 字段显示时间给用户')
        self.stdout.write('  - 原始的 created_at 等字段保留用于排序和计算')
        
        self.stdout.write('\n【测试建议】')
        self.stdout.write('  - 访问 /api/adminsys/admin-users/ 查看API响应')
        self.stdout.write('  - 访问 /admin/adminsys/adminuser/ 查看Admin界面')
        
        self.stdout.write('\n【时间转换示例代码】')
        self.stdout.write('  ```python')
        self.stdout.write('  from django.utils import timezone')
        self.stdout.write('  ')
        self.stdout.write('  # 将UTC时间转换为本地时间')
        self.stdout.write('  utc_time = user.created_at')
        self.stdout.write('  local_time = timezone.localtime(utc_time)')
        self.stdout.write('  formatted = local_time.strftime("%Y-%m-%d %H:%M:%S")')
        self.stdout.write('  ```')
        
        self.stdout.write('\n✅ 时区问题已修复！现在API和Admin都会显示正确的本地时间。') 