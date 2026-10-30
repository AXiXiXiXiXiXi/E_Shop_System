# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
            ALTER TABLE cart_item 
            ADD COLUMN product_variant_id bigint NULL,
            ADD CONSTRAINT fk_product_variant 
            FOREIGN KEY (product_variant_id) 
            REFERENCES product_productvariant(id);
            ''',
            reverse_sql='''
            ALTER TABLE cart_item 
            DROP FOREIGN KEY fk_product_variant,
            DROP COLUMN product_variant_id;
            '''
        ),
    ] 