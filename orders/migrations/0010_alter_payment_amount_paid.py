# Generated by Django 5.0.3 on 2024-04-12 06:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_alter_wallet_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='amount_paid',
            field=models.PositiveIntegerField(),
        ),
    ]
