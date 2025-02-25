# Generated by Django 5.1 on 2024-12-07 04:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0013_alter_returnrequest_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Payment_Failed', 'Payment Failed'), ('Processing', 'Processing'), ('On_Hold', 'On Hold'), ('Shipped', 'Shipped'), ('On_the_Way', 'On the Way'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled'), ('Return_Requested', 'Return Requested'), ('Returned', 'Returned'), ('Refunded', 'Refunded')], default='Pending', max_length=24),
        ),
    ]
