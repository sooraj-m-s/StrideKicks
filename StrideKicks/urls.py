from django.urls import path, include


urlpatterns = [
    path('auth/', include('social_django.urls', namespace='social')),
    path('create/', include('users.urls')),
    path('admin/', include('admin.urls')),
    path('', include('homepage.urls')),
    path('category/', include('category.urls')),
    path('brand/', include('brand.urls')),
    path('product/', include('product.urls')),
    path('userpanel/', include('userpanel.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('coupon/', include('coupon.urls')),
    path('wallet/', include('wallet.urls')),
    path('reviews/', include('reviews.urls')),
]

