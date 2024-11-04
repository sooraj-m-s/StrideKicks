from django.urls import path
from . import views

urlpatterns = [
    path('brand/', views.brand_list, name='brand'),
    path('brand/add/', views.add_brand, name='add_brand'),
    path('brand/edit/<int:brand_id>/', views.edit_brand, name='edit_brand'),
    path('brand/delete/<int:brand_id>/', views.delete_brand, name='delete_brand'),
    path('brand/toggle/<int:brand_id>/', views.toggle_brand_status, name='toggle_brand_status'),
]
