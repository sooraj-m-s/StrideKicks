from django.contrib.auth import login
from django.shortcuts import redirect
from .models import Users


def create_user(strategy, details, backend, request, user=None, *args, **kwargs):
    fields = {
        'email': details.get('email'),
        'first_name': details.get('first_name'),
        'last_name': details.get('last_name'),
    }

    if not fields['email']:
        return
    
    existing_user = Users.objects.filter(email=fields['email']).first()
    if existing_user:
        login(request, existing_user, backend='social_core.backends.google.GoogleOAuth2')
        if not existing_user.mobile_no:
            return redirect('enter_mobile')
        return redirect('/')

    # If the user does not exist, create a new user
    user = Users(
        email=fields['email'],
        first_name=fields['first_name'],
        last_name=fields['last_name'],
        status='Active'
    )
    user.set_unusable_password()  # No password for social login users
    user.save()

    login(request, user, backend='social_core.backends.google.GoogleOAuth2')
    return redirect('enter_mobile')
