# Generated by Django 5.1 on 2024-11-16 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='cancellation_reason',
            field=models.CharField(blank=True, choices=[('OPM', 'Order Placed by Mistake'), ('CMM', 'Changed My Mind'), ('DTL', 'Delivery Time Was Too Long'), ('ILN', 'Item No Longer Needed'), ('OWI', 'Ordered Wrong Item'), ('OFS', 'Item Not Available or Out of Stock'), ('DP', 'Received Damaged Product'), ('RII', 'Received Incorrect Item'), ('NME', "Product Didn't Meet Expectations"), ('QC', 'Quality Concerns'), ('SCI', 'Size/Color Issue')], max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='custom_cancellation_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='is_cancelled',
            field=models.BooleanField(default=False),
        ),
    ]
