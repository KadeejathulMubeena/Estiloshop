# Generated by Django 5.0.3 on 2024-04-07 06:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0009_productoffer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productattribute',
            name='offer_price',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
