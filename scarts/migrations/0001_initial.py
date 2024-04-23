# Generated by Django 5.0.3 on 2024-03-30 10:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shop', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cart_id', models.CharField(blank=True, max_length=250)),
                ('date_added', models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coupon_code', models.CharField(max_length=50, unique=True)),
                ('discount', models.PositiveIntegerField(default=50)),
                ('expiration_date', models.DateTimeField()),
                ('max_usage', models.PositiveIntegerField(default=1)),
                ('used_count', models.PositiveIntegerField(default=0)),
                ('minimum_amount', models.PositiveIntegerField(default=500)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('is_active', models.BooleanField(default=True)),
                ('cart', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='scarts.cart')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='shop.product')),
                ('product_attribute', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='shop.productattribute')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
