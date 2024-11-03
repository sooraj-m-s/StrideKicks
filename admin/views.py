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
    product = {
        'products': products,
        'first_name': first_name,
    }
    return render(request, 'admin_product.html', product)


@login_required
def add_product(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name', '').strip()
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        description = request.POST.get('description', '').strip()
        product_price = request.POST.get('product_price')
        sale_price = request.POST.get('sale_price')
        quantity = request.POST.get('quantity')
        color = request.POST.get('color', '').strip()
        size = request.POST.get('size')
        images = request.FILES.getlist('images')

        errors = {}

        if not product_name or re.search(r'[^a-zA-Z0-9\s]', product_name):
            errors['product_name'] = 'Product name should contain only text and numbers.'

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

        if not color or re.search(r'[^a-zA-Z\s]', color):
            errors['color'] = 'Color should contain only text.'

        try:
            size = int(size)
            if size <= 0:
                errors['size'] = 'Size should be a positive integer.'
        except ValueError:
            errors['size'] = 'Size should be a valid number.'

        if len(images) < 3 or len(images) > 10:
            errors['images'] = 'Please select 3 to 10 images.'

        if not product_price or float(product_price) <= 0:
            errors['product_price'] = 'Product price must be a positive number.'

        if not sale_price or float(sale_price) <= 0:
            errors['sale_price'] = 'Sale price must be a positive number.'

        if errors:
            for field, error in errors.items():
                messages.error(request, f"{field.capitalize()}: {error}")
            return render(request, 'add_product.html', {
                'categories': Category.objects.all(),
                'brands': Brand.objects.all(),
                'first_name': request.user.first_name,
                'form_data': request.POST
            })

        try:
            product = Product(
                product_name=product_name,
                category_id=category_id,
                brand_id=brand_id,
                description=description,
                product_price=product_price,
                sale_price=sale_price,
                quantity=quantity,
                color=color,
                size=size
            )
            product.save()

            for image in images:
                img = Image.open(image)
                img = img.convert('RGB')
                img.thumbnail((500, 500))
                thumb_io = io.BytesIO()
                img.save(thumb_io, 'JPEG', quality=85)
                
                product_image = ProductImage(product=product)
                product_image.image.save(
                    f'{product.id}_{image.name}',
                    ContentFile(thumb_io.getvalue()),
                    save=False
                )
                product_image.save()

            messages.success(request, 'Product added successfully!')
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')

    categories = Category.objects.all()
    brands = Brand.objects.all()
    data = {
        'categories': categories,
        'brands': brands,
        'first_name': request.user.first_name
    }
    return render(request, 'add_product.html', data)


@login_required(login_url='admin_login')
def admin_orders(request):
    return render(request, 'admin_orders.html')


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
