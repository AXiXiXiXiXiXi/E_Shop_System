# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_initial'),
        ('cart', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
            -- 检查product_id字段是否存在，如果不存在则添加
            SET @column_exists = (
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'cart_item'
                AND column_name = 'product_id'
                AND table_schema = DATABASE()
            );
            
            SET @sql = IF(@column_exists = 0, 
                'ALTER TABLE cart_item ADD COLUMN product_id bigint NULL', 
                'SELECT "product_id field already exists"'
            );
            
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            
            -- 检查product_variant_id字段是否存在，如果不存在则添加
            SET @column_exists = (
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'cart_item'
                AND column_name = 'product_variant_id'
                AND table_schema = DATABASE()
            );
            
            SET @sql = IF(@column_exists = 0, 
                'ALTER TABLE cart_item ADD COLUMN product_variant_id bigint NULL', 
                'SELECT "product_variant_id field already exists"'
            );
            
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            ''',
            reverse_sql=''
        ),
    ] 