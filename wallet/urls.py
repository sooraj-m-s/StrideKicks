from django.urls import path
from . import views


urlpatterns = [
    path('', views.wallet_view, name='wallet'),
    path('offer-management/', views.offer_management, name='offer_management'),
    path('create-offer/', views.create_offer, name='create_offer'),
    path('edit-offer/<int:offer_id>/', views.edit_offer, name='edit_offer'),
    path('delete-offer/<int:offer_id>/', views.delete_offer, name='delete_offer'),
]
