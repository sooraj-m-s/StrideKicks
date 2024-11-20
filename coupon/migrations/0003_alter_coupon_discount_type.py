# Generated by Django 5.1 on 2024-11-20 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0002_alter_coupon_discount_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='discount_type',
            field=models.CharField(choices=[('fixed', 'Fixed Amount'), ('percent', 'Percentage')], default='percent', max_length=10),
        ),
    ]
