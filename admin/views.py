from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import cache_control, never_cache
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from users.forms import CustomAuthenticationForm
from users.models import Users
from orders.models import Order, OrderItem
from utils.decorators import admin_required


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
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def dashboard_view(request):
    first_name = request.user.first_name.title()
    user = {
        'first_name': first_name
    }
    return render(request, 'dashboard.html', user)


@login_required(login_url='admin_login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_orders(request):
    # Get all order items with related order and user data
    order_items_list = OrderItem.objects.select_related('order__user', 'product_variant__product').order_by('-order__created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        order_items_list = order_items_list.filter(
            Q(order__order_number__istartswith=search_query) |
            Q(order__user__user_id__istartswith=search_query) |
            Q(product_variant__product__name__istartswith=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        order_items_list = order_items_list.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(order_items_list, 10)
    page = request.GET.get('page', 1)
    order_items = paginator.get_page(page)
    
    first_name = request.user.first_name.title()
    data = {
        'order_items': order_items,
        'status_choices': OrderItem.STATUS_CHOICES,
        'search_query': search_query,
        'status_filter': status_filter,
        'first_name': first_name,
    }
    return render(request, 'admin_orders.html', data)


@login_required(login_url='admin_login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_order_overview(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    other_orders = Order.objects.filter(user=order.user).exclude(id=order_id)
    status_choices = OrderItem.STATUS_CHOICES

    data = {
        'order': order,
        'other_orders': other_orders,
        'status_choices': status_choices,
    }
    return render(request, 'admin_order_overview.html', data)


@login_required(login_url='admin_login')
@admin_required
def update_order_item(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(OrderItem, id=item_id)
        item.status = request.POST.get('status')
        item.admin_note = request.POST.get('admin_note')
        item.save()
        return redirect('admin_order_overview', order_id=item.order.id) 


@login_required(login_url='admin_login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def customers_view(request):
    users = Users.objects.filter(is_superuser=False).order_by('first_name')
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
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def customer_status(request, email):
    if request.method == 'POST':
        user = get_object_or_404(Users, email=email)
        user.status = 'Blocked' if user.status == 'Active' else 'Active'
        user.save()
    return redirect('customers')


@login_required(login_url='admin_login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
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
