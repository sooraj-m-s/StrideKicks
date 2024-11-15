from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    path('about/', views.about_us, name='about'),
    path('products/', views.product_listing, name='product_listing'),
    path('products/filter/', views.filter_products, name='filter_products'),
]
