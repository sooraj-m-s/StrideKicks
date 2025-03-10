# Generated by Django 5.1 on 2024-11-14 08:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0003_alter_cartitem_variant'),
        ('product', '0017_remove_productvariant_product_productvarient'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='variant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cart_items', to='product.productvarient'),
        ),
    ]
