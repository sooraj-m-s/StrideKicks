from django.urls import path
from . import views

urlpatterns = [
    path('', views.products_view, name='products'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('add/', views.add_product, name='add_product'),
    path('cancel-add/', views.cancel_add_product, name='cancel_add_product'),
    path('edit/<int:product_id>/', views.edit_product, name='edit_product'),
]
