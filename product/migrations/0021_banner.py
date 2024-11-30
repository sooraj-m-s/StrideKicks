# Generated by Django 5.1 on 2024-11-28 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0020_productimage_variant'),
    ]

    operations = [
        migrations.CreateModel(
            name='Banner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('image', models.URLField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]