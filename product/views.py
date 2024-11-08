from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.views.decorators.cache import cache_control
import cloudinary
import cloudinary.uploader
import re, json
from django.db import transaction
from .models import Product, ProductVarient, ProductImage
from brand.models import Brand
from category.models import Category
from utils.decorators import admin_required
from django.db.models import Min


# Create your views here.


@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def products_view(request):
    first_name = request.user.first_name.title()
    products = Product.objects.filter(is_deleted=False).prefetch_related('variants', 'images')
    varients = ProductVarient.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)

    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    if search_query:
        products = products.filter(Q(name__icontains=search_query))
    if category_id:
        products = products.filter(category_id=category_id)
    products = products.annotate(min_sale_price=Min('variants__sale_price'))

    data = {
        'first_name': first_name,
        'products': products,
        'varients': varients,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id

    }
    return render(request, 'admin_product.html', data)


@transaction.atomic
@login_required(login_url='admin_login')
@require_POST
def delete_product(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        product.is_deleted = True
        product.deleted_at = timezone.now()
        product.save()
        return JsonResponse({'success': True, 'message': 'Product deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@transaction.atomic
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        description = request.POST.get('description', '').strip()
        quantity = request.POST.get('quantity')
        variants = json.loads(request.POST.get('variants', '[]'))

        errors = {}

        if not name or re.search(r'[^a-zA-Z0-9\s]', name):
            errors['name'] = 'Product name should contain only text and numbers.'

        if not category_id:
            errors['category'] = 'Please select a category.'

        if not brand_id:
            errors['brand'] = 'Please select a brand.'

        if len(description) < 20:
            errors['description'] = f'{20 - len(description)} more characters needed.'

        try:
            quantity = int(quantity)
            if quantity <= 0 or quantity > 1000:
                errors['quantity'] = 'Quantity should be between 1 and 1000.'
        except ValueError:
            errors['quantity'] = 'Quantity should be a valid number.'

        if not variants:
            errors['variants'] = 'At least one variant is required.'

        for variant in variants:
            if not variant['color'].strip():
                errors['color'] = 'Color is required for all variants.'
            if not variant['size']:
                errors['size'] = 'Size is required for all variants.'
            try:
                actual_price = float(variant['actual_price'])
                if actual_price <= 0:
                    errors['actual_price'] = 'Product price must be a positive number.'
            except ValueError:
                errors['actual_price'] = 'Please enter a valid price.'

            if variant['sale_price']:
                try:
                    sale_price = float(variant['sale_price'])
                    if sale_price <= 0:
                        errors['sale_price'] = 'Sale price must be a positive number.'
                    if sale_price >= actual_price:
                        errors['sale_price'] = 'Sale price must be less than actual price.'
                except ValueError:
                    errors['sale_price'] = 'Please enter a valid price.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        try:
            product = Product(
                name=name,
                category_id=category_id,
                brand_id=brand_id,
                description=description,
                quantity=quantity,
                is_deleted=False
            )
            product.save()

            for i, variant in enumerate(variants):
                product_variant = ProductVarient(
                    product=product,
                    color=variant['color'].strip(),
                    size=variant['size'],
                    actual_price=variant['actual_price'],
                    sale_price=variant['sale_price'] if variant['sale_price'] else None
                )
                product_variant.save()

                # Handle images for each variant
                variant_images = request.FILES.getlist(f'variant_image{i + 1}[]')
                for index, image in enumerate(variant_images):
                    cloudinary_response = cloudinary.uploader.upload(image, 
                        folder=f"product_images/{product.id}/variant_{i + 1}",
                        public_id=f"{product.id:03d}_{i + 1:02d}_{index + 1:03d}",
                        overwrite=True,
                        format="webp",
                        quality=85
                    )
                    cloudinary_url = cloudinary_response['secure_url']
                    product_image = ProductImage(
                        image=cloudinary_url, 
                        product=product,
                    )
                    product_image.save()
                
            return JsonResponse({'success': True, 'message': 'Product added successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Error, retry!'})
            # return JsonResponse({'success': False, 'errors': {'server': str(e)}})

    first_name = request.user.first_name.title()
    categories = Category.objects.filter(is_deleted=False, is_listed=True)
    brands = Brand.objects.filter(is_deleted=False, is_listed=True)
    data = {
        'first_name': first_name,
        'categories': categories,
        'brands': brands
    }
    return render(request, 'add_product.html', data)


def cancel_add_product(request):
    messages.info(request, 'Cancelled')
    return redirect('products')


@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.filter(is_deleted=False, is_listed=True)
    brands = Brand.objects.filter(is_deleted=False, is_listed=True)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        description = request.POST.get('description', '').strip()
        quantity = request.POST.get('quantity')
        new_images = request.FILES.getlist('images')
        variants = json.loads(request.POST.get('variants', '[]'))

        errors = {}

        if not name or re.search(r'[^a-zA-Z0-9\s]', name):
            errors['name'] = 'Product name should contain only text and numbers.'

        if not category_id:
            errors['category'] = 'Please select a category.'

        if not brand_id:
            errors['brand'] = 'Please select a brand.'

        if len(description) < 20:
            errors['description'] = f'{20 - len(description)} more characters needed.'

        try:
            quantity = int(quantity)
            if quantity <= 0 or quantity > 1000:
                errors['quantity'] = 'Quantity should be between 1 and 1000.'
        except ValueError:
            errors['quantity'] = 'Quantity should be a valid number.'

        if new_images and (len(new_images) + product.image.count() < 3 or len(new_images) + product.image.count() > 10):
            errors['images'] = 'Total number of images should be between 3 and 10.'

        if not variants:
            errors['variants'] = 'At least one variant is required.'

        for variant in variants:
            if not variant['color'].strip():
                errors['color'] = 'Color is required for all variants.'
            if not variant['size']:
                errors['size'] = 'Size is required for all variants.'
            try:
                actual_price = float(variant['actual_price'])
                if actual_price <= 0:
                    errors['actual_price'] = 'Product price must be a positive number.'
            except ValueError:
                errors['actual_price'] = 'Please enter a valid price.'

            if variant['sale_price']:
                try:
                    sale_price = float(variant['sale_price'])
                    if sale_price <= 0:
                        errors['sale_price'] = 'Sale price must be a positive number.'
                    if sale_price >= actual_price:
                        errors['sale_price'] = 'Sale price must be less than actual price.'
                except ValueError:
                    errors['sale_price'] = 'Please enter a valid price.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        try:
            product.name = name
            product.category_id = category_id
            product.brand_id = brand_id
            product.description = description
            product.quantity = quantity
            product.save()

            # Delete existing variants and create new ones
            product.varient.all().delete()
            for variant in variants:
                product_variant = ProductVarient(
                    product_id=product,
                    color=variant['color'].strip(),
                    size=variant['size'],
                    actual_price=variant['actual_price'],
                    sale_price=variant['sale_price'] if variant['sale_price'] else None
                )
                product_variant.save()

            if new_images:
                for index, image in enumerate(new_images):
                    cloudinary_response = cloudinary.uploader.upload(image, 
                        folder=f"product_images/{product.id}",
                        public_id=f"{product.id:03d}_{product.image.count() + index + 1:03d}",
                        overwrite=True,
                        format="webp",
                        quality=85
                    )
                    cloudinary_url = cloudinary_response['secure_url']
                    ProductImage.objects.create(product_id=product, image=cloudinary_url)

            return JsonResponse({'success': True, 'message': 'Product updated successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': {'server': str(e)}})

    first_name = request.user.first_name.title()
    data = {
        'first_name': first_name,
        'product': product,
        'categories': categories,
        'brands': brands,
    }
    return render(request, 'edit_product.html', data)
