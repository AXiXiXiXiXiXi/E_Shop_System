from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0004_auto_20250711_0000'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE TABLE IF NOT EXISTS `order_orderstatushistory` (
                `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
                `from_status` varchar(20) NOT NULL,
                `to_status` varchar(20) NOT NULL,
                `remark` longtext NOT NULL,
                `created_at` datetime(6) NOT NULL,
                `operator_id` integer NULL,
                `order_id` bigint NOT NULL,
                CONSTRAINT `order_orderstatushistory_order_id_fk` FOREIGN KEY (`order_id`) REFERENCES `order_order` (`id`),
                CONSTRAINT `order_orderstatushistory_operator_id_fk` FOREIGN KEY (`operator_id`) REFERENCES `auth_user` (`id`)
            );
            """,
            """
            DROP TABLE IF EXISTS `order_orderstatushistory`;
            """
        ),
        migrations.RunSQL(
            """
            CREATE TABLE IF NOT EXISTS `order_orderrefund` (
                `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
                `refund_number` varchar(32) NOT NULL UNIQUE,
                `type` varchar(20) NOT NULL,
                `status` varchar(20) NOT NULL,
                `reason` longtext NOT NULL,
                `refund_amount` decimal(10, 2) NOT NULL,
                `evidence_images` json NOT NULL,
                `admin_remark` longtext NOT NULL,
                `processed_at` datetime(6) NULL,
                `created_at` datetime(6) NOT NULL,
                `order_id` bigint NOT NULL,
                CONSTRAINT `order_orderrefund_order_id_fk` FOREIGN KEY (`order_id`) REFERENCES `order_order` (`id`)
            );
            """,
            """
            DROP TABLE IF EXISTS `order_orderrefund`;
            """
        )
    ] 