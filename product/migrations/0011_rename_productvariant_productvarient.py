# Generated by Django 5.1 on 2024-11-07 12:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0010_remove_productimage_product_id_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ProductVariant',
            new_name='ProductVarient',
        ),
    ]
