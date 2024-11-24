from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_to_account, name='admin_login'),
    path('dashboard/', views.dashboard_view, name='admin_dashboard'),
    path('customers/', views.customers_view, name='customers'),
    path('customers/status/<str:email>/', views.customer_status, name='customer_status'),
    path('orders/', views.admin_orders, name='orders'),
    path('order/<int:order_id>/', views.admin_order_overview, name='admin_order_overview'),
    path('order-item/update/<int:item_id>/', views.update_order_item, name='update_order_item'),
    path('sales-report/', views.sales_report, name='sales_report'),
    path('sales-report/download-pdf/', views.download_report_pdf, name='download_report_pdf'),
    path('sales-report/download-excel/', views.download_report_excel, name='download_report_excel'),
    path('settings/', views.settings_view, name='settings'),
    path('logout/', views.logout_account, name='admin_logout'),
]
