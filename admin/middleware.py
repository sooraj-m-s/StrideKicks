from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import logout
from django.contrib import messages
from social_core.exceptions import AuthCanceled


class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        excluded_paths = [reverse('login_to_account')]
        if request.path not in excluded_paths:
            if request.user.is_authenticated and request.user.status == 'Blocked':
                logout(request)
                messages.error(request, 'Your account has been blocked. Please contact customer service.')
                return redirect(settings.LOGIN_URL)

        response = self.get_response(request)
        return response


class SocialAuthExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, AuthCanceled):
            messages.error(request, "Authentication process canceled.")
            return redirect('signup')  
        return None
