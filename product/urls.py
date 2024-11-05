from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.products_view, name='products'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('add-product/', views.add_product, name='add_product'),
    path('cancel-add-product/', views.cancel_add_product, name='cancel_add_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
]
