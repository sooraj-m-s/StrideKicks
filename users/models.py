from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

# Create your models here.


class Users(AbstractBaseUser, PermissionsMixin):
    STATUS_CHOICE = [
        ('Active', 'Active'), ('Inactive', 'Inactive'), ('Blocked', 'Blocked')
    ]
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(max_length=120, unique=True)
    mobile_no = models.BigIntegerField(unique=True, null=True, blank=True)
    password = models.CharField(max_length=120)
    status = models.CharField(max_length=10, choices=STATUS_CHOICE, default='Active')
    created_at = models.DateField(auto_now_add=True)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'  #specify the unique identifier for login

