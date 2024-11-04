from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from users.forms import CustomAuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.db.models import Q
from users.models import Users
from product.models import Product, Category, Brand, ProductImage
from PIL import Image
import re, io
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone


# Create your views here.


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login_to_account(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_superuser:
                messages.error(request, 'Only admin can login here.')
                return render(request, 'admin_login.html', {'form': form})
            login(request, user)
            messages.success(request, 'Login Successful.')
            return redirect('admin_dashboard')
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
            return render(request, 'admin_login.html', {'form': form})
    else:
        form = CustomAuthenticationForm()
        return render(request, 'admin_login.html', {'form': form})


@login_required(login_url='admin_login')
def dashboard_view(request):
    # Set the first letter to uppercase and the rest to lowercase
    first_name = request.user.first_name.title()
    user = {
        'first_name': first_name
    }
    return render(request, 'dashboard.html', user)


@login_required(login_url='admin_login')
def products_view(request):
    first_name = request.user.first_name.title()
    products = Product.objects.filter(is_deleted=False)
    data = {
        'products': products,
        'first_name': first_name,
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


@login_required
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
            if images:
                main_image = images[0]
                img = Image.open(main_image)
                img = img.convert('RGB')
                img.thumbnail((500, 500))
                thumb_io = io.BytesIO()
                img.save(thumb_io, 'JPEG', quality=85)
                product.image.save(
                    f'main_{product.id}_{main_image.name}',
                    ContentFile(thumb_io.getvalue()),
                    save=True
                )
            for image in images[1:]:
                img = Image.open(image)
                img = img.convert('RGB')
                img.thumbnail((500, 500))
                thumb_io = io.BytesIO()
                img.save(thumb_io, 'JPEG', quality=85)
                
                product_image = ProductImage(product=product)
                product_image.image.save(
                    f'{product.id}_{image.name}',
                    ContentFile(thumb_io.getvalue()),
                    save=True
                )

            messages.success(request, 'Product added successfully!')
            return redirect('products')
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')

    categories = Category.objects.all()
    brands = Brand.objects.all()
    context = {
        'categories': categories,
        'brands': brands
    }
    return render(request, 'add_product.html', context)


@login_required(login_url='admin_login')
def admin_orders(request):
    return render(request, 'admin_orders.html')


def cancel_add_product(request):
    messages.info(request, 'Cancelled')
    return redirect('products')


@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    brands = Brand.objects.all()

    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        description = request.POST.get('description', '').strip()
        actual_price = request.POST.get('actual_price')
        sale_price = request.POST.get('sale_price')
        quantity = request.POST.get('quantity')
        new_images = request.FILES.getlist('images')

        # Update product
        product.name = name
        product.category_id = category_id
        product.brand_id = brand_id
        product.description = description
        product.actual_price = actual_price
        product.sale_price = sale_price
        product.quantity = quantity
        product.save()

        # Handle new images
        if new_images:
            for image in new_images:
                img = Image.open(image)
                img = img.convert('RGB')
                img.thumbnail((500, 500))
                thumb_io = io.BytesIO()
                img.save(thumb_io, 'JPEG', quality=85)
                
                product_image = ProductImage(product=product)
                product_image.image.save(
                    f'{product.id}_{image.name}',
                    ContentFile(thumb_io.getvalue()),
                    save=True
                )

        messages.success(request, 'Product updated successfully!')
        return redirect('products')

    data = {
        'product': product,
        'categories': categories,
        'brands': brands,
    }
    return render(request, 'edit_product.html', data)


@login_required(login_url='admin_login')
def customers_view(request):
    users = Users.objects.filter(is_superuser=False)
    search_query = request.GET.get('search')
    status_filter = request.GET.get('status')

    if search_query:
        users = users.filter(
            Q(first_name__istartswith=search_query) |
            Q(email__istartswith=search_query) |
            Q(mobile_no__istartswith=search_query)
        )

    if status_filter:
        users = users.filter(status=status_filter)

    first_name = request.user.first_name.title()
    context = {
        'users': users,
        'first_name': first_name
    }
    return render(request, 'customers.html', context)


@login_required(login_url='admin_login')
def customer_status(request, email):
    if request.method == 'POST':
        user = get_object_or_404(Users, email=email)
        user.status = 'Blocked' if user.status == 'Active' else 'Active'
        user.save()
    return redirect('customers')


@login_required(login_url='admin_login')
def settings_view(request):
    first_name = request.user.first_name.title()
    user = {
        'first_name': first_name
    }
    return render(request, 'admin_settings.html', user)


@never_cache
def logout_account(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out.')
        return redirect('admin_login')
