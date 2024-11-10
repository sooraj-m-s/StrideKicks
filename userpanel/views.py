from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
import re
from users.models import Users


# Create your views here.


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_profile(request):
    return render(request, 'profile.html')


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def update_profile(request):
    if request.method=='POST':
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'Session expired. Please log in again.')
            return redirect('login_to_account')
        
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        if not re.match(r"^[A-Za-z]+(?: [A-Za-z]+)*$", first_name):
            messages.error(request, 'Invalid first name, please enter a valid input.')
            return redirect('update_profile')

        if not re.match(r"^[A-Za-z]+(?: [A-Za-z]+)*$", last_name):
            messages.error(request, 'Invalid last name, please enter a valid input.')
            return redirect('update_profile')
        
        try:
            user_data = Users.objects.get(user_id=user_id)
            user_data.first_name = first_name
            user_data.last_name = last_name
            user_data.save()
            messages.success(request, 'Profile updated.')
        except Users.DoesNotExist:
            messages.error(request, 'User not found.')
        return redirect('profile')
        
    return render(request, 'update_profile.html')


def change_password(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'Session expired. Please log in again.')
            return redirect('login_to_account')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        try:
            user = Users.objects.get(user_id=user_id)

            # Check if the old password is correct
            if not check_password(old_password, user.password):
                messages.error(request, 'The old password is incorrect, please try again')
                return redirect('change_password')

            # Check if the new password and confirmation match
            if new_password != confirm_password:
                messages.error(request, 'The new passwords do not match.')
                return redirect('change_password')

            # Validate the new password (you can add more validation rules)
            if len(new_password) < 8 or new_password.isspace():
                messages.error(request, 'Password must be at least 8 characters and cannot contain only spaces.')
                return redirect('change_password')

            # Update the password
            user.password = make_password(new_password)
            user.save()

            #updating the session to prevent logout
            update_session_auth_hash(request, user)

            messages.success(request, 'Your password has been successfully changed.')
            return redirect('profile')

        except Users.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('login_to_account')

    return render(request, 'change_password.html')


def cancel_profile_update(request):
    messages.error(request, 'Update cancelled.')
    return redirect('profile')
