# Generated by Django 5.1 on 2024-12-06 13:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0012_returnrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='returnrequest',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='return_requests', to='orders.orderitem'),
        ),
    ]