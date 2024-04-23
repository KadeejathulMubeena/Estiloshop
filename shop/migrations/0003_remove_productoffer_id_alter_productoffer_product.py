# Generated by Django 5.0.3 on 2024-04-01 05:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_rename_new_price_productattribute_price_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productoffer',
            name='id',
        ),
        migrations.AlterField(
            model_name='productoffer',
            name='product',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='shop.product'),
        ),
    ]
