from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.views.decorators.cache import cache_control
from django.conf import settings
import cloudinary
import cloudinary.uploader
from PIL import Image
import re, io, os
from .models import Product, ProductImage
from brand.models import Brand
from category.models import Category
from utils.decorators import admin_required


# Create your views here.


@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def products_view(request):
    first_name = request.user.first_name.title()
    products = Product.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
        )
    if category_id:
        products = products.filter(id=category_id)
    data = {
        'first_name': first_name,
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id

    }
    return render(request, 'admin_product.html', data)


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


@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        description = request.POST.get('description', '').strip()
        actual_price = request.POST.get('actual_price')
        sale_price = request.POST.get('sale_price')
        quantity = request.POST.get('quantity')
        images = request.FILES.getlist('images')

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

        try:
            actual_price = float(actual_price)
            if actual_price <= 0:
                errors['actual_price'] = 'Product price must be a positive number.'
        except ValueError:
            errors['actual_price'] = 'Please enter a valid price.'

        if sale_price:
            try:
                sale_price = float(sale_price)
                if sale_price <= 0:
                    errors['sale_price'] = 'Sale price must be a positive number.'
                if sale_price >= actual_price:
                    errors['sale_price'] = 'Sale price must be less than actual price.'
            except ValueError:
                errors['sale_price'] = 'Please enter a valid price.'

        if len(images) < 3 or len(images) > 10:
            errors['images'] = 'Please select 3 to 10 images.'

        if errors:
            for field, error in errors.items():
                messages.error(request, f"{field.capitalize()}: {error}")
            return render(request, 'add_product.html', {
                'categories': Category.objects.all(),
                'brands': Brand.objects.all(),
                'form_data': request.POST
            })

        try:
            product = Product(
                name=name,
                category_id=category_id,
                brand_id=brand_id,
                description=description,
                actual_price=actual_price,
                sale_price=sale_price,
                quantity=quantity,
                is_deleted=False
            )
            product.save()


            for index, image in enumerate(images):
                print(f"{product.id:03d}_{index+1:03d}")
                # Upload image to Cloudinary
                cloudinary_response = cloudinary.uploader.upload(image, 
                    folder=f"product_images/{product.id}",
                    public_id=f"{product.id:03d}_{index+1:03d}",
                    overwrite=True,
                    format="webp",
                    quality=85
                )
                cloudinary_url = cloudinary_response['secure_url']
                product_image = ProductImage(image=cloudinary_url,product_id=product)
                product_image.save()
                
            messages.success(request, 'Product added successfully!')
            return redirect('products')
        except Exception as e:
            Product.objects.filter(id=product.id).delete()
            messages.error(request, f'Error adding product: {str(e)}')

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
    categories = Category.objects.all()
    brands = Brand.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        description = request.POST.get('description', '').strip()
        actual_price = request.POST.get('actual_price')
        sale_price = request.POST.get('sale_price')
        quantity = request.POST.get('quantity')
        new_images = request.FILES.getlist('images')

        product.name = name
        product.category_id = category_id
        product.brand_id = brand_id
        product.description = description
        product.actual_price = actual_price
        product.sale_price = sale_price
        product.quantity = quantity
        product.save()

        if new_images:
            for image in new_images:
                # Upload image to Cloudinary
                cloudinary_response = cloudinary.uploader.upload(image, 
                    folder=f"product_images/{product.id}",
                    public_id=f"{product.id}_{image.name}",
                    overwrite=True,
                    format="webp",
                    quality=85
                )
                
                cloudinary_url = cloudinary_response['secure_url']
                ProductImage.objects.create(product=product, image=cloudinary_url)

        messages.success(request, 'Product updated successfully!')
        return redirect('products')

    first_name = request.user.first_name.title()
    data = {
        'first_name': first_name,
        'product': product,
        'categories': categories,
        'brands': brands,
    }
    return render(request, 'edit_product.html', data)
