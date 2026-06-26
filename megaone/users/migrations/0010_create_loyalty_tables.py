from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_loyalty_card_models'),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE TABLE IF NOT EXISTS `loyalty_cards_loyaltycard` ("
                "  `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,"
                "  `card_number` varchar(50) NOT NULL UNIQUE,"
                "  `total_points` integer NOT NULL,"
                "  `used_points` integer NOT NULL,"
                "  `remaining_points` integer NOT NULL,"
                "  `qr_token` varchar(64) NOT NULL UNIQUE,"
                "  `qr_code_image` varchar(100) NULL,"
                "  `card_pdf` varchar(100) NULL,"
                "  `card_image` varchar(100) NULL,"
                "  `status` varchar(20) NOT NULL,"
                "  `first_card_popup_shown` bool NOT NULL,"
                "  `created_at` datetime(6) NOT NULL,"
                "  `updated_at` datetime(6) NOT NULL,"
                "  `user_id` bigint NULL,"
                "  CONSTRAINT `loyalty_cards_loyaltycard_user_id_fk`"
                "    FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`)"
                "    ON DELETE CASCADE"
                ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;",
            reverse_sql="DROP TABLE IF EXISTS `loyalty_cards_loyaltycard`;",
        ),
        migrations.RunSQL(
            sql="CREATE TABLE IF NOT EXISTS `loyalty_cards_loyaltytransaction` ("
                "  `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,"
                "  `order_number` varchar(50) NULL,"
                "  `earned_points` integer NOT NULL,"
                "  `redeemed_points` integer NOT NULL,"
                "  `remaining_balance` integer NOT NULL,"
                "  `transaction_type` varchar(20) NOT NULL,"
                "  `created_at` datetime(6) NOT NULL,"
                "  `card_id` bigint NOT NULL,"
                "  CONSTRAINT `loyalty_cards_loyaltytransaction_card_id_fk`"
                "    FOREIGN KEY (`card_id`) REFERENCES `loyalty_cards_loyaltycard` (`id`)"
                "    ON DELETE CASCADE"
                ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;",
            reverse_sql="DROP TABLE IF EXISTS `loyalty_cards_loyaltytransaction`;",
        ),
    ]
