# Generated by Django 5.1 on 2024-11-14 14:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0019_rename_productvarient_productvariant'),
    ]

    operations = [
        migrations.AddField(
            model_name='productimage',
            name='variant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='images', to='product.productvariant'),
        ),
    ]
