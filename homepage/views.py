from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Min, Max, Q
from django.core.serializers.json import DjangoJSONEncoder
import json
from product.models import Product, ProductVariant
from category.models import Category
from brand.models import Brand
from userpanel.models import Wishlist


# Create your views here.


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home(request):
    latest_products = Product.objects.filter(is_deleted=False).order_by('-created_at')[:5]
    featured_products = Product.objects.filter(is_deleted=False, variants__sale_price__isnull=False).distinct()[:5]
    trending_products = Product.objects.filter(is_deleted=False).order_by('-total_quantity')[:5]
    
    data = {
        'latest_products': latest_products,
        'featured_products': featured_products,
        'trending_products': trending_products,
    }
    
    return render(request, 'home_page.html', data)


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def product_detail(request, product_id):
    # product = get_object_or_404(Product, id=product_id)
    product = get_object_or_404(Product.objects.select_related('brand', 'category').prefetch_related('variants', 'images'), id=product_id)
    # related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    related_products = Product.objects.filter(is_deleted=False).exclude(id=product.id)[:4]
    variants = product.variants.all()

    available_variants = [
        {
            'id': variant.id,
            'size': variant.size,
            'color': variant.color,
            'sale_price': str(variant.sale_price),
            'actual_price': str(variant.actual_price),
            'quantity': variant.quantity,
        }
        for variant in variants
    ]
    is_wishlisted = Wishlist.objects.filter(user=request.user, variant__product=product).exists()
    data = {
        'product': product,
        'related_products': related_products,
        'available_variants': json.dumps(available_variants, cls=DjangoJSONEncoder),
        'is_wishlisted': is_wishlisted,
    }
    
    return render(request, 'product_detail.html', data)


@login_required
def get_variant_details(request):
    product_id = request.GET.get('product_id')
    size = request.GET.get('size')
    color = request.GET.get('color')
    
    try:
        variant = ProductVariant.objects.get(product_id=product_id, size=size, color=color)
        data = {
            'id': variant.id,
            'sale_price': str(variant.sale_price),
            'actual_price': str(variant.actual_price),
            'quantity': variant.quantity,
            'found': True,
        }
    except ProductVariant.DoesNotExist:
        data = {'found': False}
    
    return JsonResponse(data)


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def about_us(request):
    return render(request, 'about.html')


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def product_listing(request):
    categories = Category.objects.filter(is_deleted=False, is_listed=True)
    brands = Brand.objects.filter(is_deleted=False, is_listed=True)
    price_range = Product.objects.filter(is_deleted=False).aggregate(
        min_price=Min('variants__sale_price'),
        max_price=Max('variants__sale_price')
    )
    all_products = Product.objects.filter(is_deleted=False).prefetch_related('variants', 'images').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(all_products, 12)
    page_number = request.GET.get('page', 1)
    products = paginator.get_page(page_number)

    data = {
        'categories': categories,
        'brands': brands,
        'min_price': price_range['min_price'],
        'max_price': price_range['max_price'],
        'products': products,
    }
    
    return render(request, 'product_listing.html', data)


def filter_products(request):
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort', 'newest')
    category_ids = request.GET.get('categories', '').split(',')
    brand_ids = request.GET.get('brands', '').split(',')
    ratings = request.GET.get('ratings', '').split(',')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    page = request.GET.get('page', 1)
    products = Product.objects.filter(is_deleted=False).prefetch_related('variants', 'images')

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if category_ids and category_ids[0]:
        products = products.filter(category_id__in=category_ids)

    if brand_ids and brand_ids[0]:
        products = products.filter(brand_id__in=brand_ids)

    if ratings and ratings[0]:
        products = products.filter(rating__gte=min(ratings))

    if min_price and max_price:
        products = products.filter(
            variants__sale_price__gte=min_price,
            variants__sale_price__lte=max_price
        )
    if sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'name_asc':
        products = products.order_by('name')
    elif sort_by == 'name_desc':
        products = products.order_by('-name')
    elif sort_by == 'price_asc':
        products = products.order_by('variants__sale_price')
    elif sort_by == 'price_desc':
        products = products.order_by('-variants__sale_price')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    products = products.distinct()

    # Pagination
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(page)
    html = render_to_string(
        'product_grid.html',
        {'products': page_obj},
        request=request
    )

    return JsonResponse({
        'success': True,
        'html': html,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'total_pages': paginator.num_pages,
        'current_page': page_obj.number,
    })
