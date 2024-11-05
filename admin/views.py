from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from users.forms import CustomAuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.db.models import Q
from users.models import Users


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
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def dashboard_view(request):
    first_name = request.user.first_name.title()
    user = {
        'first_name': first_name
    }
    return render(request, 'dashboard.html', user)


@login_required(login_url='admin_login')
def admin_orders(request):
    first_name = request.user.first_name.title()
    user = {
        'first_name': first_name
    }
    return render(request, 'admin_orders.html', user)


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
