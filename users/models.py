from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UsersManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        return self.create_user(email, password, **extra_fields)

    def change_password(self, email, new_password):
        """Shell helper: Users.objects.change_password('a@b.com', 'NewPass@123')"""
        user = self.get(email=self.normalize_email(email))
        user.set_password(new_password)
        user.save(update_fields=['password'])
        return user

    def update_user(self, email, **fields):
        """Shell helper: Users.objects.update_user('a@b.com', first_name='John', status='Blocked')"""
        user = self.get(email=self.normalize_email(email))
        valid_fields = {f.name for f in self.model._meta.concrete_fields} - {'user_id', 'created_at'}

        unknown = set(fields) - valid_fields
        if unknown:
            raise ValueError(f"Unknown field(s): {', '.join(sorted(unknown))}")

        if 'password' in fields:
            user.set_password(fields.pop('password'))
            fields['password'] = user.password  # keep the hashed value
        if 'email' in fields:
            fields['email'] = self.normalize_email(fields['email'])

        for name, value in fields.items():
            setattr(user, name, value)
        user.full_clean(exclude=['password'])  # validates choices, max_length, uniqueness
        user.save(update_fields=list(fields))
        return user


class Users(AbstractBaseUser, PermissionsMixin):
    STATUS_CHOICE = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Blocked', 'Blocked'),
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
    is_active = models.BooleanField(default=True)

    objects = UsersManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

