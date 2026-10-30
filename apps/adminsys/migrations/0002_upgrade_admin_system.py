# Generated manually for AdminSys upgrade

from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone

class Migration(migrations.Migration):

    dependencies = [
        ('adminsys', '0001_initial'),
    ]

    operations = [
        # 为Role模型添加新字段
        migrations.AddField(
            model_name='role',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='是否启用'),
        ),
        migrations.AddField(
            model_name='role',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now, verbose_name='创建时间'),
            preserve_default=False,
        ),
        
        # 为AdminUser模型添加新字段
        migrations.AddField(
            model_name='adminuser',
            name='email',
            field=models.EmailField(blank=True, null=True, verbose_name='邮箱'),
        ),
        migrations.AddField(
            model_name='adminuser',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='手机号'),
        ),
        migrations.AddField(
            model_name='adminuser',
            name='real_name',
            field=models.CharField(blank=True, max_length=50, verbose_name='真实姓名'),
        ),
        migrations.AddField(
            model_name='adminuser',
            name='last_login',
            field=models.DateTimeField(blank=True, null=True, verbose_name='最后登录时间'),
        ),
        migrations.AddField(
            model_name='adminuser',
            name='login_count',
            field=models.PositiveIntegerField(default=0, verbose_name='登录次数'),
        ),
        
        # 为Permission模型添加新字段
        migrations.AddField(
            model_name='permission',
            name='description',
            field=models.TextField(blank=True, verbose_name='权限描述'),
        ),
        migrations.AddField(
            model_name='permission',
            name='module',
            field=models.CharField(default='system', max_length=50, verbose_name='所属模块'),
        ),
        migrations.AddField(
            model_name='permission',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='是否启用'),
        ),
        migrations.AddField(
            model_name='permission',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now, verbose_name='创建时间'),
            preserve_default=False,
        ),
        
        # 修改字段属性
        migrations.AlterField(
            model_name='role',
            name='name',
            field=models.CharField(max_length=50, unique=True, verbose_name='角色名称'),
        ),
        migrations.AlterField(
            model_name='role',
            name='description',
            field=models.TextField(blank=True, verbose_name='角色描述'),
        ),
        migrations.AlterField(
            model_name='adminuser',
            name='username',
            field=models.CharField(max_length=150, unique=True, verbose_name='用户名'),
        ),
        migrations.AlterField(
            model_name='adminuser',
            name='password',
            field=models.CharField(max_length=128, verbose_name='密码'),
        ),
        migrations.AlterField(
            model_name='adminuser',
            name='role',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='adminsys.role', verbose_name='角色'),
        ),
        migrations.AlterField(
            model_name='adminuser',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='是否启用'),
        ),
        migrations.AlterField(
            model_name='adminuser',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='创建时间'),
        ),
        migrations.AlterField(
            model_name='adminuser',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='permission',
            name='name',
            field=models.CharField(max_length=100, verbose_name='权限名称'),
        ),
        migrations.AlterField(
            model_name='permission',
            name='codename',
            field=models.CharField(max_length=100, unique=True, verbose_name='权限代码'),
        ),
        migrations.AlterField(
            model_name='permission',
            name='roles',
            field=models.ManyToManyField(blank=True, related_name='permissions', to='adminsys.role', verbose_name='关联角色'),
        ),
        
        # 添加模型元数据
        migrations.AlterModelOptions(
            name='role',
            options={'ordering': ['name'], 'verbose_name': '管理员角色', 'verbose_name_plural': '管理员角色'},
        ),
        migrations.AlterModelOptions(
            name='adminuser',
            options={'ordering': ['-created_at'], 'verbose_name': '管理员用户', 'verbose_name_plural': '管理员用户'},
        ),
        migrations.AlterModelOptions(
            name='permission',
            options={'ordering': ['module', 'name'], 'verbose_name': '系统权限', 'verbose_name_plural': '系统权限'},
        ),
    ] 