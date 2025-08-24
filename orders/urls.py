from django.urls import path
from . import views


urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('cancel-product/<int:item_id>/', views.cancel_product, name='cancel_product'),
    path('return-product/<int:item_id>/', views.return_product, name='return_product'),
    path('stripe/callback/', views.stripe_callback, name='stripe_callback'),
    path('stripe-checkout/<int:order_id>/', views.stripe_checkout, name='stripe_checkout'),
    path('invoice/<int:item_id>/download/', views.download_invoice, name='download_invoice'),
]

