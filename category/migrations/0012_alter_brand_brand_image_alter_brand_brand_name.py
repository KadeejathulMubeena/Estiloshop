# Generated by Django 5.0.3 on 2024-04-16 02:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0011_brand_soft_delete'),
    ]

    operations = [
        migrations.AlterField(
            model_name='brand',
            name='brand_image',
            field=models.ImageField(upload_to='brand'),
        ),
        migrations.AlterField(
            model_name='brand',
            name='brand_name',
            field=models.CharField(max_length=100),
        ),
    ]
