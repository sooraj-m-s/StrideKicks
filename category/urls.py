from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.category_list, name='category'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    path('categories/toggle/<int:category_id>/', views.toggle_category_status, name='toggle_category_status'),
]
