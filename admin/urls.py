from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_to_account, name='admin_login'),
    path('dashboard/', views.dashboard_view, name='admin_dashboard'),
    path('customers/', views.customers_view, name='customers'),
    path('customers/status/<str:email>/', views.customer_status, name='customer_status'),
    path('orders/', views.admin_orders, name='orders'),
    path('products/', views.products_view, name='products'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('add-product/', views.add_product, name='add_product'),
    path('cancel-add-product/', views.cancel_add_product, name='cancel_add_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('settings/', views.settings_view, name='settings'),
    path('logout/', views.logout_account, name='admin_logout'),
]
