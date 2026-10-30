# Generated manually to fix migration issues

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='分类名称')),
                ('description', models.TextField(blank=True, null=True, verbose_name='分类描述')),
                ('sort_order', models.IntegerField(default=0, verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='product.category', verbose_name='父分类')),
            ],
            options={
                'verbose_name': '商品分类',
                'verbose_name_plural': '商品分类',
                'db_table': 'product_category',
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Merchant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='商家名称')),
                ('description', models.TextField(verbose_name='商家描述')),
                ('contact_email', models.EmailField(max_length=254, verbose_name='联系邮箱')),
                ('contact_phone', models.CharField(max_length=20, verbose_name='联系电话')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '商家',
                'verbose_name_plural': '商家',
                'db_table': 'product_merchant',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='商品名称')),
                ('description', models.TextField(blank=True, null=True, verbose_name='商品描述')),
                ('brand', models.CharField(blank=True, max_length=100, null=True, verbose_name='品牌')),
                ('image', models.CharField(blank=True, max_length=200, null=True, verbose_name='主图')),
                ('images', models.JSONField(blank=True, null=True, verbose_name='图片集')),
                ('status', models.CharField(choices=[('active', '上架'), ('inactive', '下架'), ('deleted', '删除')], default='active', max_length=20, verbose_name='状态')),
                ('is_featured', models.BooleanField(default=False, verbose_name='是否推荐')),
                ('rating', models.DecimalField(decimal_places=2, default=0, max_digits=3, verbose_name='评分')),
                ('sales_count', models.IntegerField(default=0, verbose_name='销量')),
                ('view_count', models.IntegerField(default=0, verbose_name='浏览量')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='product.category', verbose_name='商品分类')),
                ('merchant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.merchant', verbose_name='商家')),
            ],
            options={
                'verbose_name': '商品',
                'verbose_name_plural': '商品',
                'db_table': 'product_product',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='变体名称')),
                ('sku', models.CharField(max_length=100, unique=True, verbose_name='SKU')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='价格')),
                ('original_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='原价')),
                ('stock', models.IntegerField(default=0, verbose_name='库存')),
                ('weight', models.DecimalField(blank=True, decimal_places=3, max_digits=8, null=True, verbose_name='重量(kg)')),
                ('attributes', models.JSONField(blank=True, null=True, verbose_name='属性')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='product.product', verbose_name='商品')),
            ],
            options={
                'verbose_name': '商品变体',
                'verbose_name_plural': '商品变体',
                'db_table': 'product_productvariant',
            },
        ),
    ] 