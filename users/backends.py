from django.contrib.auth.backends import BaseBackend
from .models import Users
from django.contrib.auth.hashers import check_password


class EmailBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None):
        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            return None

        # Check password
        if check_password(password, user.password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return Users.objects.get(pk=user_id)
        except Users.DoesNotExist:
            return None
