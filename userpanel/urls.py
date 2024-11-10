from django.urls import path, include
from . import views

urlpatterns = [
    path('profile/', views.user_profile, name='profile'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('cancel/', views.cancel_profile_update, name='cancel_profile_update'),
    path('change-password/', views.change_password, name='change_password'),
]