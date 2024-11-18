"""
URL configuration for StrideKicks project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include

urlpatterns = [
    path('auth/', include('social_django.urls', namespace='social')),
    path('create', include('users.urls')),
    path('admin/', include('admin.urls')),
    path('', include('homepage.urls')),
    path('category/', include('category.urls')),
    path('brand/', include('brand.urls')),
    path('product/', include('product.urls')),
    path('userpanel/', include('userpanel.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    # path('reviews/', include('reviews.urls')),
    # path('wallet/', include('wallet.urls')),
    # path('coupon/', include('coupon.urls')),
]
