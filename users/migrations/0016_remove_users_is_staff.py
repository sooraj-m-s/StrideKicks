# Generated by Django 5.1 on 2024-11-04 12:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_users_is_active_users_is_staff'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='users',
            name='is_staff',
        ),
    ]
