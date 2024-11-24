from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import cache_control, never_cache
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import HttpResponse
from io import BytesIO
from users.forms import CustomAuthenticationForm
from users.models import Users
from orders.models import Order, OrderItem
from utils.decorators import admin_required

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import xlsxwriter


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
            username = user.first_name.title()
            messages.success(request, f"Login Successful. Welcome, {username}!")
            return redirect('admin_dashboard')
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
            return render(request, 'admin_login.html', {'form': form})
    else:
        form = CustomAuthenticationForm()
        return render(request, 'admin_login.html', {'form': form})


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def dashboard_view(request):
    first_name = request.user.first_name.title()
    user = {
        'first_name': first_name
    }
    return render(request, 'dashboard.html', user)


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_orders(request):
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


@login_required
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


@login_required
@admin_required
def update_order_item(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(OrderItem, id=item_id)
        item.status = request.POST.get('status')
        item.admin_note = request.POST.get('admin_note')
        item.save()
        return redirect('admin_order_overview', order_id=item.order.id) 


@login_required
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

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(users, 5)
    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)
    if status_filter:
        users = users.filter(status=status_filter)

    first_name = request.user.first_name.title()
    context = {
        'users': users_page,
        'first_name': first_name
    }
    return render(request, 'customers.html', context)


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def customer_status(request, email):
    if request.method == 'POST':
        user = get_object_or_404(Users, email=email)
        user.status = 'Blocked' if user.status == 'Active' else 'Active'
        user.save()
    return redirect('customers')


@login_required
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


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def sales_report(request):
    # Get filter parameters
    report_type = request.GET.get('type', 'daily')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Calculate date range based on report type
    today = timezone.now().date()
    if report_type == 'daily':
        start_date = today
        end_date = today
    elif report_type == 'weekly':
        start_date = today - timedelta(days=7)
        end_date = today
    elif report_type == 'monthly':
        start_date = today.replace(day=1)
        end_date = today
    elif report_type == 'yearly':
        start_date = today.replace(month=1, day=1)
        end_date = today
    elif report_type == 'custom':
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            start_date = today
            end_date = today

    # Query orders within date range
    orders = Order.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).select_related('user').order_by('-created_at')

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(orders, 5)
    try:
        orders_page = paginator.page(page)
    except PageNotAnInteger:
        orders_page = paginator.page(1)
    except EmptyPage:
        orders_page = paginator.page(paginator.num_pages)

    # Calculate totals
    total_amount = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    total_discount = orders.aggregate(total=Sum('discount'))['total'] or 0

    context = {
        'orders': orders_page,
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date,
        'total_amount': total_amount,
        'total_discount': total_discount,
        'first_name': request.user.first_name,
    }
    
    return render(request, 'sales_report.html', context)

@login_required
def download_report_excel(request):
    # Get filter parameters
    report_type = request.GET.get('type', 'daily')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Query orders
    orders = Order.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).select_related('user').prefetch_related('items__product_variant__product')

    # Create the HttpResponse object
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sales_report.xlsx"'

    # Create workbook and worksheet
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Add headers
    headers = [
        'Product Name', 'Quantity', 'Unit Price', 'Total Price', 'Discount',
        'Coupon Deduction', 'Final Amount', 'Order Date', 'Customer Name',
        'Payment Method', 'Delivery Status'
    ]
    
    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'border': 1,
        'bg_color': '#f2f2f2'
    })
    
    cell_format = workbook.add_format({
        'border': 1
    })

    # Write headers
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
        worksheet.set_column(col, col, 15)  # Set column width

    # Write data
    row = 1
    for order in orders:
        for item in order.items.all():
            worksheet.write(row, 0, item.product_variant.product.name, cell_format)
            worksheet.write(row, 1, item.quantity, cell_format)
            worksheet.write(row, 2, float(item.price), cell_format)
            worksheet.write(row, 3, float(item.total_price), cell_format)
            worksheet.write(row, 4, float(order.discount) if order.discount else 0, cell_format)
            worksheet.write(row, 5, float(order.coupon.discount_amount) if order.coupon else 0, cell_format)
            worksheet.write(row, 6, float(order.total_amount), cell_format)
            worksheet.write(row, 7, order.created_at.strftime('%d/%m/%Y'), cell_format)
            worksheet.write(row, 8, order.user.get_full_name(), cell_format)
            worksheet.write(row, 9, order.get_payment_method_display(), cell_format)
            worksheet.write(row, 10, item.status, cell_format)
            row += 1

    workbook.close()
    output.seek(0)
    response.write(output.read())
    return response

@login_required
def download_report_pdf(request):
    # Get filter parameters
    report_type = request.GET.get('type', 'daily')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Query orders
    orders = Order.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).select_related('user').prefetch_related('items__product_variant__product')

    # Create the HttpResponse object
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    # Create the PDF object
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Add title
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    elements.append(Paragraph("Sales Report", title_style))
    elements.append(Spacer(1, 20))

    # Create report for each order
    for index, order in enumerate(orders, 1):
        # Add report header
        elements.append(Paragraph(f"Report {index}", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        # Add order details
        elements.append(Paragraph(f"Order Date: {order.created_at.strftime('%d/%m/%Y')}", styles['Normal']))
        elements.append(Paragraph(f"Customer Name: {order.user.get_full_name()}", styles['Normal']))
        elements.append(Paragraph(f"Payment Method: {order.get_payment_method_display()}", styles['Normal']))
        
        # Add product details header
        elements.append(Paragraph("Product Details", styles['Heading3']))
        
        # Create product details table
        product_data = [['Product Name', 'Order Status', 'Quantity', 'Unit Price (RS)', 'Total Price (RS)']]
        for item in order.items.all():
            product_data.append([
                item.product_variant.product.name,
                item.status,
                str(item.quantity),
                str(item.price),
                str(item.total_price)
            ])
        
        # Style the table
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        product_table = Table(product_data)
        product_table.setStyle(table_style)
        elements.append(product_table)
        elements.append(Spacer(1, 10))
        
        # Add discount and final amount details
        elements.append(Paragraph(f"Final Coupon Discount: RS. {order.discount if order.discount else 0:.2f}", styles['Normal']))
        elements.append(Paragraph(f"Final Product Discount: RS. {order.coupon.discount_amount if order.coupon else 0:.2f}", styles['Normal']))
        elements.append(Paragraph(f"Final Amount: RS. {order.total_amount:.2f}", styles['Normal']))
        elements.append(Spacer(1, 20))

    # Add total order amount at the end
    total_amount = sum(order.total_amount for order in orders)
    elements.append(Paragraph("Total Order amount:", styles['Heading3']))
    elements.append(Paragraph(f"RS. {total_amount:.2f}", styles['Normal']))

    # Build the PDF document
    doc.build(elements)
    return response
