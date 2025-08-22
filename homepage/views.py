from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import cache_control
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Min, Max, Q, Avg, Count
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import AnonymousUser
import json, re, logging
from django.contrib import messages
from product.models import Product, ProductVariant
from category.models import Category
from brand.models import Brand
from userpanel.models import Wishlist
from reviews.models import ProductReview
from .models import ContactUs


logger = logging.getLogger(__name__)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home(request):
    try:
        latest_products = Product.objects.filter(is_deleted=False).order_by('-created_at')[:5]
        featured_products = Product.objects.filter(is_deleted=False, variants__sale_price__isnull=False).distinct()[:5]
        trending_products = Product.objects.filter(is_deleted=False).order_by('-total_quantity')[:5]
        
        # get review
        for product_list in [latest_products, featured_products, trending_products]:
            for product in product_list:
                product.avg_rating = ProductReview.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg'] or 0
                product.review_count = ProductReview.objects.filter(product=product).count()
        data = {
            'latest_products': latest_products,
            'featured_products': featured_products,
            'trending_products': trending_products,
        }
    except Exception as e:
        logger.error(f"Error in home view: {e}")
        messages.error(request, "Sorry, we couldn't load products at this time. Please try again later.")
        data = {
            'latest_products': [],
            'featured_products': [],
            'trending_products': [],
        }
    
    return render(request, 'home_page.html', data)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def product_detail(request, product_id):
    try:
        product = get_object_or_404(Product.objects.select_related('brand', 'category').prefetch_related('variants', 'images'), id=product_id)
        related_products = Product.objects.filter(is_deleted=False).exclude(id=product.id)[:4]
        variants = product.variants.all()

        available_variants = []
        for variant in variants:
            variant_images = [img.image for img in variant.images.filter(is_deleted=False)]
            if not variant_images:  # If no variant images, use product images
                variant_images = [img.image for img in product.images.filter(is_deleted=False)]
                
            available_variants.append({
                'id': variant.id,
                'size': variant.size,
                'color': variant.color,
                'sale_price': str(variant.sale_price),
                'actual_price': str(variant.actual_price),
                'quantity': variant.quantity,
                'images': variant_images
            })
        if isinstance(request.user, AnonymousUser):
            is_wishlisted = False
        else:
            is_wishlisted = Wishlist.objects.filter(user=request.user, variant__product=product).exists()

        # get review
        reviews = ProductReview.objects.filter(product=product).order_by('-created_at')
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        review_count = reviews.count()
        related_products = related_products.annotate(avg_rating=Avg('reviews__rating'), review_count=Count('reviews'))
        
        data = {
            'product': product,
            'related_products': related_products,
            'available_variants': json.dumps(available_variants, cls=DjangoJSONEncoder),
            'is_wishlisted': is_wishlisted,
            'reviews': reviews,
            'avg_rating': avg_rating,
            'review_count': review_count,
        }
    except Exception as e:
        logger.error(f"Error in product_detail: {e}")
        messages.error(request, "An error occurred while loading the product details. Please try again later.")
        data = {
            'product': None,
            'related_products': [],
            'available_variants': '[]',
            'is_wishlisted': False,
            'reviews': [],
            'avg_rating': 0,
            'review_count': 0,
        }
    
    return render(request, 'product_detail.html', data)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
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
        logger.error(f"Variant not found: product_id={product_id}, size={size}, color={color}")
        data = {'found': False}
    
    return JsonResponse(data)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def about_us(request):
    return render(request, 'about.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if not re.match(r"^[A-Za-z]{3,}(?: [A-Za-z]+)*$", name):
            messages.error(request, 'Invalid name, please enter a valid input.')
            return redirect('contact_us')

        if not re.match(r"^[A-Za-z\._\-0-9]+@[A-Za-z]+\.[a-z]{2,4}$", email):
            messages.error(request, 'Invalid email, please enter a valid emali.')
            return redirect('contact_us')
        
        try:
            ContactUs.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            messages.success(request, 'Your response has been submitted successfully!')
            return redirect('home')
        except Exception as e:
            logger.error(f"Error in contact_us: {e}")
            messages.error(request, 'An error occurred while submitting your response. Please try again later.')
            return redirect('contact_us')
    
    return render(request, 'contact_us.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def product_listing(request):
    try:
        categories = Category.objects.filter(is_deleted=False, is_listed=True)
        brands = Brand.objects.filter(is_deleted=False, is_listed=True)
        price_range = Product.objects.filter(is_deleted=False).aggregate(
            min_price=Min('variants__sale_price'),
            max_price=Max('variants__sale_price')
        )
        all_products = Product.objects.filter(is_deleted=False).prefetch_related('variants', 'images').order_by('-created_at')
        
        for product in all_products:
            product.avg_rating = ProductReview.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg'] or 0
            product.review_count = ProductReview.objects.filter(product=product).count()
            
            # Check if product is in user's wishlist
            if request.user.is_authenticated:
                product.is_wishlisted = Wishlist.objects.filter(
                    user=request.user, 
                    variant__product=product
                ).exists()
            else:
                product.is_wishlisted = False
        
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
    except Exception as e:
        logger.error(f"Error in product_listing: {e}")
        messages.error(request, "An error occurred while loading products. Please try again later.")
        data = {
            'categories': [],
            'brands': [],
            'min_price': None,
            'max_price': None,
            'products': [],
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
    products = Product.objects.filter(is_deleted=False).prefetch_related('variants', 'images', 'reviews')

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if category_ids and category_ids[0]:
        products = products.filter(category_id__in=category_ids)

    if brand_ids and brand_ids[0]:
        products = products.filter(brand_id__in=brand_ids)

    products = products.annotate(avg_rating=Avg('reviews__rating'), review_count=Count('reviews'))
    
    if ratings and ratings[0]:
        # Filter by minimum rating
        min_rating = min([int(r) for r in ratings if r.isdigit()])
        products = products.filter(avg_rating__gte=min_rating)

    if min_price and max_price:
        try:
            min_price_val = float(min_price)
            max_price_val = float(max_price)
            products = products.filter(
                variants__sale_price__gte=min_price_val,
                variants__sale_price__lte=max_price_val
            )
        except (ValueError, TypeError):
            pass  # Skip price filtering if invalid values
    
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
        products = products.order_by('-avg_rating')
    
    products = products.distinct()

    for product in products:
        if request.user.is_authenticated:
            product.is_wishlisted = Wishlist.objects.filter(
                user=request.user, 
                variant__product=product
            ).exists()
        else:
            product.is_wishlisted = False

    # Pagination
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(page)
    html = render_to_string('product_grid.html', {'products': page_obj, 'user': request.user}, request=request)

    return JsonResponse({
        'success': True,
        'html': html,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'total_pages': paginator.num_pages,
        'current_page': page_obj.number,
    })

