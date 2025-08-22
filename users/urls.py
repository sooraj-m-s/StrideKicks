from django.urls import path
from . import views


urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
    path('', views.login_to_account, name='login_to_account'),
    path('logout/', views.logout_account, name='logout_account'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('enter-mobile/', views.enter_mobile, name='enter_mobile'),
]

