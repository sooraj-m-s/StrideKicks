from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
import re, random, json
from .models import Users
from .forms import CustomAuthenticationForm


# Create your views here.

def signup_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        mobile_no = request.POST.get('mobile_no')
        password = request.POST.get('password')
        retype_password = request.POST.get('retype_password')

        if not re.match(r"^[A-Za-z\._\-0-9]+@[A-Za-z]+\.[a-z]{2,4}$", email):
            messages.error(request, 'Invalid email, please enter a valid emali.')
            return redirect('signup')

        if len(password) < 8 or password.isspace():
            messages.error(request, 'Password must be at least 8 characters and cannot contain only spaces.')
            return redirect('signup')

        #check if email of mob is already exists
        if Users.objects.filter(email=email).exists() or Users.objects.filter(mobile_no=mobile_no).exists():
            messages.error(request, 'Email or phone numeber already registered')
            return redirect('signup')
        
        if password != retype_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')
        
        #create a new user
        otp = random.randint(100000, 999999)
        otp_expiry = (timezone.now() + timedelta(minutes=5)).isoformat()

        request.session['user_data'] = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'mobile_no': mobile_no,
            'password': password,
            'retype_password': retype_password,
            'otp': otp,
            'otp_expiry': otp_expiry
        }
        send_mail(
            'Verify your email - expires in 5 minutes',
            f'Your verification code is: {otp}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        
        messages.info(request, 'Please check your email for the verification code.')
        return redirect('verify_email')

    google_auth_url = reverse('social:begin', args=['google-oauth2'])
    return render(request, 'sign_up.html', {'google_auth_url': google_auth_url})

@csrf_exempt
def verify_email(request):
    user_data = request.session.get('user_data')
    first_name = user_data.get('first_name').title() if user_data else None
    
    now = timezone.now()
    otp_expiry = user_data.get('otp_expiry')
    if otp_expiry:
        otp_expiry = timezone.datetime.fromisoformat(otp_expiry)
        time_left = otp_expiry - now
        expiration_seconds = max(0, int(time_left.total_seconds()))
        expiration_time = f"{expiration_seconds // 60:02d}:{expiration_seconds % 60:02d}"
    else:
        expiration_seconds = 0
        expiration_time = "00:00"

    resend_time = user_data.get('resend_time')
    if resend_time:
        resend_time = timezone.datetime.fromisoformat(resend_time)
        resend_countdown = max(0, int((resend_time - now).total_seconds()))
        can_resend = resend_countdown == 0
    else:
        resend_countdown = 0
        can_resend = True

    if request.method == 'POST':
        data = json.loads(request.body)
        code = data.get('code')

        if not user_data:
            return JsonResponse({'success': False, 'error': 'Session expired. Please sign up again.'}, status=400)

        if str(user_data.get('otp')) != str(code):  # Convert both to strings for comparison
            return JsonResponse({'success': False, 'error': 'Invalid verification code.'}, status=400)

        if now > otp_expiry:
            return JsonResponse({'success': False, 'error': 'Verification code expired.'}, status=400)

        # If verification is successful, create a new user
        new_user = Users(
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            email=user_data['email'],
            mobile_no=user_data['mobile_no'],
            password=make_password(user_data['password']),
        )
        new_user.save()

        # Clear the session data after verification and user creation
        if 'user_data' in request.session:
                del request.session['user_data']
                request.session.modified = True
        return JsonResponse({'success': True, 'message': 'Verification successful. Account created!'})

    context = {
        'first_name': first_name,
        'expiration_time': expiration_time,
        'expiration_seconds': expiration_seconds,
        'resend_countdown': resend_countdown,
        'can_resend': can_resend,
    }
    return render(request, 'verify_email.html', context)

def resend_otp(request):
    if request.method == 'POST':
        user_data = request.session.get('user_data')
        
        if not user_data:
            return JsonResponse({'success': False, 'message': 'User session expired. Please sign up again.'}, status=400)
        
        # Generate a new OTP and update the expiration time
        new_otp = random.randint(100000, 999999)
        new_expiry_time = timezone.now() + timedelta(minutes=5)
        new_resend_time = timezone.now() + timedelta(seconds=30)

        #update the session with the new OTP and expiry time
        user_data['otp'] = new_otp
        user_data['otp_expiry'] = new_expiry_time.isoformat()
        user_data['resend_time'] = new_resend_time.isoformat()
        request.session['user_data'] = user_data  #save updated data back to the session

        send_mail(
            'Verify your email - expires in 5 minutes',
            f'Your verification code is: {new_otp}',
            settings.EMAIL_HOST_USER,
            [user_data['email']],
            fail_silently=False,
        )
        return JsonResponse({'success': True, 'message': 'A new verification code has been sent to your email.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login_to_account(request):
    if request.user.is_authenticated:
        return redirect('account_overview')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Login Successful.')
            return redirect('account_overview')
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
            return render(request, 'login.html', {'form': form})
    else:
        form = CustomAuthenticationForm()
        google_auth_url = reverse('social:begin', args=['google-oauth2'])
        return render(request, 'login.html', {'form': form, 'google_auth_url': google_auth_url})


def logout_account(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out.')
        return redirect('login_to_account')

@login_required
def account_overview(request):
    return render(request, 'account_overview.html')
