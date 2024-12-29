from django.contrib.auth import login
from django.shortcuts import redirect
from .models import Users
from django.contrib import messages


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
        username = existing_user.first_name.title()
        if not existing_user.mobile_no:
            messages.success(request, f"Welcome back, {username}! Please add your mobile number to continue.")
            return redirect('enter_mobile')
        
        messages.success(request, f"Welcome back, {username}! You have successfully logged in!")
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
    username = user.first_name.title()
    messages.success(request, f"Account created successfully! Welcome, {username}. Please add your mobile number to continue.")
    return redirect('enter_mobile')
