"""
初始化管理员系统基础数据
使用方法: python manage.py init_admin_data
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.adminsys.models import Role, AdminUser, Permission
from apps.adminsys.permissions import Permissions

class Command(BaseCommand):
    help = '初始化管理员系统基础数据（角色、权限、默认管理员）'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            dest='reset',
            help='重置所有数据（危险操作）',
        )
        parser.add_argument(
            '--admin-username',
            type=str,
            default='admin',
            help='默认管理员用户名（默认: admin）',
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='Admin123456',
            help='默认管理员密码（默认: Admin123456）',
        )
    
    def handle(self, *args, **options):
        reset = options['reset']
        admin_username = options['admin_username']
        admin_password = options['admin_password']
        
        self.stdout.write(self.style.SUCCESS('开始初始化管理员系统数据...'))
        
        try:
            with transaction.atomic():
                if reset:
                    self.stdout.write(self.style.WARNING('⚠️  正在清除现有数据...'))
                    AdminUser.objects.all().delete()
                    Role.objects.all().delete()
                    Permission.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS('✓ 现有数据已清除'))
                
                # 创建权限
                self.create_permissions()
                
                # 创建角色
                super_admin_role, admin_role, operator_role = self.create_roles()
                
                # 创建默认管理员
                self.create_default_admin(super_admin_role, admin_username, admin_password)
                
                self.stdout.write(self.style.SUCCESS('\n🎉 管理员系统初始化完成！'))
                self.show_summary(admin_username, admin_password)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 初始化失败: {str(e)}'))
            raise e
    
    def create_permissions(self):
        """创建系统权限"""
        self.stdout.write('📋 正在创建系统权限...')
        
        permissions_data = [
            # 用户管理权限
            ('查看用户', Permissions.VIEW_USER, '查看管理员用户列表', 'user'),
            ('添加用户', Permissions.ADD_USER, '创建新的管理员用户', 'user'),
            ('修改用户', Permissions.CHANGE_USER, '编辑管理员用户信息', 'user'),
            ('删除用户', Permissions.DELETE_USER, '删除管理员用户', 'user'),
            
            # 角色权限管理
            ('查看角色', Permissions.VIEW_ROLE, '查看角色列表', 'role'),
            ('添加角色', Permissions.ADD_ROLE, '创建新角色', 'role'),
            ('修改角色', Permissions.CHANGE_ROLE, '编辑角色信息', 'role'),
            ('删除角色', Permissions.DELETE_ROLE, '删除角色', 'role'),
            
            # 权限管理
            ('查看权限', Permissions.VIEW_PERMISSION, '查看权限列表', 'permission'),
            ('添加权限', Permissions.ADD_PERMISSION, '创建新权限', 'permission'),
            ('修改权限', Permissions.CHANGE_PERMISSION, '编辑权限信息', 'permission'),
            ('删除权限', Permissions.DELETE_PERMISSION, '删除权限', 'permission'),
            
            # 订单管理权限
            ('查看订单', Permissions.VIEW_ORDER, '查看订单列表', 'order'),
            ('修改订单', Permissions.CHANGE_ORDER, '编辑订单状态', 'order'),
            ('删除订单', Permissions.DELETE_ORDER, '删除订单', 'order'),
            
            # 产品管理权限
            ('查看产品', Permissions.VIEW_PRODUCT, '查看产品列表', 'product'),
            ('添加产品', Permissions.ADD_PRODUCT, '创建新产品', 'product'),
            ('修改产品', Permissions.CHANGE_PRODUCT, '编辑产品信息', 'product'),
            ('删除产品', Permissions.DELETE_PRODUCT, '删除产品', 'product'),
            
            # 会员管理权限
            ('查看会员', Permissions.VIEW_MEMBER, '查看会员列表', 'member'),
            ('修改会员', Permissions.CHANGE_MEMBER, '编辑会员信息', 'member'),
            ('调整积分', Permissions.ADJUST_POINTS, '调整会员积分', 'member'),
            
            # 优惠券管理权限
            ('查看优惠券', Permissions.VIEW_COUPON, '查看优惠券列表', 'coupon'),
            ('添加优惠券', Permissions.ADD_COUPON, '创建优惠券', 'coupon'),
            ('修改优惠券', Permissions.CHANGE_COUPON, '编辑优惠券', 'coupon'),
            ('删除优惠券', Permissions.DELETE_COUPON, '删除优惠券', 'coupon'),
            
            # 系统管理权限
            ('系统设置', Permissions.SYSTEM_SETTINGS, '管理系统设置', 'system'),
            ('查看日志', Permissions.VIEW_LOGS, '查看系统日志', 'system'),
            ('数据备份', Permissions.BACKUP_DATA, '备份系统数据', 'system'),
        ]
        
        created_count = 0
        for name, codename, description, module in permissions_data:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    'name': name,
                    'description': description,
                    'module': module,
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ 创建权限: {name}')
        
        self.stdout.write(self.style.SUCCESS(f'✓ 创建了 {created_count} 个权限'))
        return Permission.objects.all()
    
    def create_roles(self):
        """创建角色"""
        self.stdout.write('👑 正在创建角色...')
        
        # 超级管理员角色（拥有所有权限）
        super_admin_role, created = Role.objects.get_or_create(
            name='超级管理员',
            defaults={
                'description': '拥有系统所有权限的超级管理员',
                'is_active': True
            }
        )
        if created:
            # 分配所有权限
            super_admin_role.permissions.set(Permission.objects.all())
            self.stdout.write('  ✓ 创建超级管理员角色（拥有所有权限）')
        
        # 普通管理员角色（基础管理权限）
        admin_role, created = Role.objects.get_or_create(
            name='普通管理员',
            defaults={
                'description': '拥有基础管理权限的普通管理员',
                'is_active': True
            }
        )
        if created:
            # 分配基础权限
            basic_permissions = Permission.objects.filter(
                codename__in=[
                    Permissions.VIEW_USER, Permissions.VIEW_ROLE, Permissions.VIEW_PERMISSION,
                    Permissions.VIEW_ORDER, Permissions.CHANGE_ORDER,
                    Permissions.VIEW_PRODUCT, Permissions.ADD_PRODUCT, Permissions.CHANGE_PRODUCT,
                    Permissions.VIEW_MEMBER, Permissions.CHANGE_MEMBER,
                    Permissions.VIEW_COUPON, Permissions.ADD_COUPON, Permissions.CHANGE_COUPON
                ]
            )
            admin_role.permissions.set(basic_permissions)
            self.stdout.write('  ✓ 创建普通管理员角色（基础权限）')
        
        # 操作员角色（只能查看）
        operator_role, created = Role.objects.get_or_create(
            name='操作员',
            defaults={
                'description': '只能查看数据的操作员',
                'is_active': True
            }
        )
        if created:
            # 只分配查看权限
            view_permissions = Permission.objects.filter(
                codename__in=[
                    Permissions.VIEW_USER, Permissions.VIEW_ROLE, Permissions.VIEW_PERMISSION,
                    Permissions.VIEW_ORDER, Permissions.VIEW_PRODUCT, 
                    Permissions.VIEW_MEMBER, Permissions.VIEW_COUPON
                ]
            )
            operator_role.permissions.set(view_permissions)
            self.stdout.write('  ✓ 创建操作员角色（只读权限）')
        
        self.stdout.write(self.style.SUCCESS('✓ 角色创建完成'))
        return super_admin_role, admin_role, operator_role
    
    def create_default_admin(self, super_admin_role, username, password):
        """创建默认超级管理员"""
        self.stdout.write('👤 正在创建默认管理员...')
        
        # 检查是否已存在
        if AdminUser.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'  ⚠️  用户 {username} 已存在，跳过创建'))
            return
        
        try:
            admin_user = AdminUser(
                username=username,
                email='admin@example.com',
                real_name='系统管理员',
                role=super_admin_role,
                is_active=True
            )
            admin_user.set_password(password)
            admin_user.save()
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ 创建默认管理员: {username}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ 创建管理员失败: {str(e)}'))
            raise e
    
    def show_summary(self, username, password):
        """显示初始化摘要"""
        roles_count = Role.objects.count()
        permissions_count = Permission.objects.count()
        users_count = AdminUser.objects.count()
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('📊 初始化摘要'))
        self.stdout.write('='*50)
        self.stdout.write(f'角色数量: {roles_count}')
        self.stdout.write(f'权限数量: {permissions_count}')
        self.stdout.write(f'管理员数量: {users_count}')
        self.stdout.write('\n🔑 默认管理员账户信息:')
        self.stdout.write(f'  用户名: {username}')
        self.stdout.write(f'  密码: {password}')
        self.stdout.write('\n📝 使用说明:')
        self.stdout.write('  1. 请立即修改默认管理员密码')
        self.stdout.write('  2. 可以通过 Django Admin 管理角色和权限')
        self.stdout.write(f'  3. Admin 地址: http://localhost:8000/admin/')
        self.stdout.write('  4. 建议为不同职能创建专门的角色')
        self.stdout.write('='*50) 