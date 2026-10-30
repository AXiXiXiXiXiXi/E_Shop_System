from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0005_create_missing_tables'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderrefund',
            name='coupon_returned',
            field=models.BooleanField(default=False, help_text='是否已退还优惠券'),
        ),
        migrations.AddField(
            model_name='orderrefund',
            name='coupon_returned_at',
            field=models.DateTimeField(blank=True, help_text='优惠券退还时间', null=True),
        ),
        migrations.AddField(
            model_name='orderrefund',
            name='coupon_code',
            field=models.CharField(blank=True, help_text='退还的优惠券代码', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='orderrefund',
            name='coupon_value',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='优惠券价值', max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='orderrefund',
            name='coupon_type',
            field=models.CharField(blank=True, help_text='优惠券类型', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='orderrefund',
            name='coupon_min_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='优惠券最低消费金额', max_digits=10, null=True),
        ),
    ] 