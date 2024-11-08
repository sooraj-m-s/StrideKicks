from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from product.models import Product, ProductVarient, ProductImage


# Create your views here.


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home(request):
    latest_products = Product.objects.filter(is_deleted=False).order_by('-created_at')[:5]
    featured_products = Product.objects.filter(is_deleted=False, variants__sale_price__isnull=False).distinct()[:5]
    trending_products = Product.objects.filter(is_deleted=False).order_by('-quantity')[:5]
    
    data = {
        'latest_products': latest_products,
        'featured_products': featured_products,
        'trending_products': trending_products,
    }
    
    return render(request, 'home_page.html', data)


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    related_products = Product.objects.all().exclude(id=product.id)[:4]
    data = {
        'product': product,
        'related_products': related_products,
    }
    
    return render(request, 'product_detail.html', data)
