# Generated by Django 5.0.3 on 2024-04-01 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_remove_productoffer_id_alter_productoffer_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='productoffer',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
