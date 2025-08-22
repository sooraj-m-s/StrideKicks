from django.urls import path
from . import views


urlpatterns = [
    path('', views.products_view, name='products'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('add/', views.add_product, name='add_product'),
    path('cancel-add/', views.cancel_add_product, name='cancel_add_product'),
    path('edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('banner_management/', views.banner_management, name='banner_management'),
    path('add_banner/', views.add_banner, name='add_banner'),
    path('get_banner/<int:banner_id>/', views.get_banner, name='get_banner'),
    path('update_banner/<int:banner_id>/', views.update_banner, name='update_banner'),
    path('delete_banner/<int:banner_id>/', views.delete_banner, name='delete_banner'),
]

