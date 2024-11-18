# Generated by Django 5.1 on 2024-11-14 08:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0014_alter_product_total_quantity'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productvarient',
            name='product',
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color', models.CharField(max_length=225)),
                ('size', models.CharField(choices=[('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')], max_length=2)),
                ('quantity', models.PositiveIntegerField()),
                ('actual_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('sale_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='product.product')),
            ],
        ),
    ]