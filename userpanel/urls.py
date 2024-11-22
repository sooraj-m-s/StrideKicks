from django.urls import path, include
from . import views

urlpatterns = [
    path('profile/', views.user_profile, name='profile'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('cancel/', views.cancel_profile_update, name='cancel_profile_update'),
    path('change-password/', views.change_password, name='change_password'),
    path('manage-address/', views.manage_address, name='manage_address'),
    path('add-address/', views.add_address, name='add_address'),
    path('edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('set-default-address/<int:address_id>/', views.set_default_address, name='set_default_address'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('is_wishlisted/<int:product_id>/', views.is_wishlisted, name='is_wishlisted'),
]
