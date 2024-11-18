# Generated by Django 5.1 on 2024-11-17 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_orderitem_note_admin'),
    ]

    operations = [
        migrations.RenameField(
            model_name='orderitem',
            old_name='note_admin',
            new_name='admin_note',
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('CC', 'Credit Card'), ('RP', 'Razor Pay'), ('PP', 'PayPal'), ('BT', 'Bank Transfer'), ('COD', 'Cash on Delivery')], max_length=4),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Processing', 'Processing'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled'), ('Returned', 'Returned')], default='Pending', max_length=10),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='cancellation_reason',
            field=models.CharField(blank=True, choices=[('OPM', 'Order Placed by Mistake'), ('CMM', 'Changed My Mind'), ('DTL', 'Delivery Time Was Too Long'), ('ILN', 'Item No Longer Needed'), ('OWI', 'Ordered Wrong Item'), ('OFS', 'Item Not Available or Out of Stock'), ('DP', 'Received Damaged Product'), ('RII', 'Received Incorrect Item'), ('NME', "Product Didn't Meet Expectations"), ('QC', 'Quality Concerns'), ('SCI', 'Size/Color Issue')], max_length=4, null=True),
        ),
    ]