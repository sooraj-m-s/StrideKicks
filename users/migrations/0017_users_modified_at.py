# Generated by Django 5.1 on 2025-01-03 18:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_remove_users_is_staff'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='modified_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
