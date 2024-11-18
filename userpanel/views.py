from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
import re
from django.core.exceptions import ValidationError
from django.utils import timezone
from users.models import Users
from .models import Address


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


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
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


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def cancel_profile_update(request):
    messages.error(request, 'Update cancelled.')
    return redirect('profile')


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def manage_address(request):
    addresses = Address.objects.filter(user_id=request.user, is_deleted=False)
    states = Address.STATE_CHOICES
    data = {
        'addresses': addresses,
        'states': states
    }
    return render(request, 'manage_address.html', data)


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user_id=request.user)
    if not address.default_address:
        address.is_deleted = True
        address.deleted_at = timezone.now()
        address.save()
        messages.success(request, 'Address removed successfully!')
    else:
        messages.error(request, 'Cannot delete default address.')
    return redirect('manage_address')


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_address(request):
    context = {
        'states': Address.STATE_CHOICES,
        'form_data': {},
        'errors': {}
    }
    
    if request.method == 'POST':
        form_data = {
            'full_name': request.POST.get('full_name'),
            'mobile_no': request.POST.get('mobile_no'),
            'pin_code': request.POST.get('pin_code'),
            'address': request.POST.get('address'),
            'street': request.POST.get('street'),
            'landmark': request.POST.get('landmark'),
            'city': request.POST.get('city'),
            'state': request.POST.get('state'),
            'default_address': request.POST.get('default_address') == 'on'
        }
        context['form_data'] = form_data

        try:
            address = Address(user_id=request.user, **form_data)
            address.full_clean()
            
            if address.default_address:
                Address.objects.filter(user_id=request.user).update(default_address=False)
            
            address.save()
            messages.success(request, 'Address added successfully!')
            return redirect('manage_address')
        except ValidationError as ve:
            context['errors'] = ve.message_dict
        except Exception as e:
            messages.error(request, f'Error adding address: {str(e)}')

    return render(request, 'add_address.html', context)


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user_id=request.user, is_deleted=False)
    
    if request.method == 'POST':
        try:
            address.full_name = request.POST.get('full_name')
            address.mobile_no = request.POST.get('mobile_no')
            address.pin_code = request.POST.get('pin_code')
            address.address = request.POST.get('address')
            address.street = request.POST.get('street')
            address.landmark = request.POST.get('landmark')
            address.city = request.POST.get('city')
            address.state = request.POST.get('state')
            new_default = request.POST.get('default_address') == 'on'
            
            if new_default and not address.default_address:
                Address.objects.filter(user_id=request.user).update(default_address=False)
                address.default_address = True
            address.full_clean()
            address.save()
            messages.success(request, 'Address updated successfully!')
            return redirect('manage_address')
        except ValidationError as ve:
            for field, error_list in ve.message_dict.items():
                for error in error_list:
                    if field == 'mobile_no' and 'Invalid Mobile Number.' in error:
                        messages.error(request, "Invalid Mobile Number.")
                    else:
                        messages.error(request, "Invalid PIN Number.")
                    return redirect('manage_address')
        except Exception as e:
            messages.error(request, 'Error updating address. Please try again.')
    
    data = {
        'address': address,
        'states': Address.STATE_CHOICES
    }
    return render(request, 'edit_address.html', data)


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def set_default_address(request, address_id):
    try:
        address = get_object_or_404(Address, id=address_id, user_id=request.user, is_deleted=False)
        Address.objects.filter(user_id=request.user).update(default_address=False)
        address.default_address = True
        address.save()
        messages.success(request, 'Default address updated successfully!')
    except Exception:
        messages.error(request, 'Address not found.')
    return redirect('manage_address')