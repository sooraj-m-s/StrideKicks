from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_cart, name='view_cart'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
]
