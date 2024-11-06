from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('verify_email/', views.verify_email, name='verify_email'),
    path('resend_otp/', views.resend_otp, name='resend_otp'),
    path('', views.account_overview, name='account_overview'),
    path('login_to_account/', views.login_to_account, name='login_to_account'),
    path('logout/', views.logout_account, name='logout_account')
]
