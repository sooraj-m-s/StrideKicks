# Generated by Django 5.1 on 2024-11-20 09:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0001_initial'),
        ('orders', '0007_order_razorpay_order_id_order_razorpay_payment_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='coupon',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='coupon.coupon'),
        ),
    ]
