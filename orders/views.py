from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.db.models import Prefetch
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse
from .models import Order, OrderItem
from cart.models import Cart
from userpanel.models import Address
import uuid


# Create your views here.


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        return redirect('view_cart')

    addresses = Address.objects.filter(user_id=request.user, is_deleted=False)
    
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method')
        
        if not address_id or not payment_method:
            messages.error(request, "Please select both address and payment method.")
            return redirect('checkout')
        
        address = Address.objects.get(id=address_id, user_id=request.user)
        
        with transaction.atomic():
            # Check stock availability
            for item in cart.items.all():
                if item.quantity > item.variant.quantity:
                    messages.error(request, f"Not enough stock for {item.product.name} - {item.variant}")
                    return redirect('checkout')
            
            subtotal = sum(item.price * item.quantity for item in cart.items.all())
            # Create order
            order = Order.objects.create(
                user=request.user,
                order_number=uuid.uuid4().hex[:12].upper(),
                payment_method=payment_method,
                payment_status=False,
                subtotal=subtotal,
                total_amount=cart.total_price,
                shipping_address=address,
                shipping_cost=cart.delivery_charge or 0,
            )
            
            # Create order items and update stock
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product_variant=item.variant,
                    quantity=item.quantity,
                    price=item.price,
                    original_price=item.variant.actual_price,
                )
                item.variant.quantity -= item.quantity
                item.variant.save()
            
            # Clear the cart
            cart.delete()
            
            messages.success(request, f"Order placed successfully. Your order number is {order.order_number}")
            return redirect('order_success', order_id=order.id)

    context = {
        'cart': cart,
        'addresses': addresses,
        'payment_methods': Order.PAYMENT_METHOD_CHOICES,
    }
    return render(request, 'checkout.html', context)


@login_required(login_url='login_to_account')
def order_success(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    return render(request, 'order_success.html', {'order': order})


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def my_orders(request):
    orders = Order.objects.filter(user=request.user)
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    if search_query:
        orders = orders.filter(order_number__icontains=search_query)

    order_items_query = OrderItem.objects.all()
    if status_filter:
        order_items_query = order_items_query.filter(status=status_filter)
    orders = orders.prefetch_related(
        Prefetch('items', queryset=order_items_query, to_attr='filtered_items')
    ).order_by('-created_at')
    if status_filter:
        orders = [order for order in orders if order.filtered_items]
    status_choices = OrderItem.STATUS_CHOICES
    data = {
        'orders': orders,
        'status_choices': status_choices,
        'search_query': search_query,
        'status_filter': status_filter,
    }

    return render(request, 'orders/my_orders.html', data)


@login_required(login_url='login_to_account')
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required(login_url='login_to_account')
def cancel_product(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    
    if request.method == 'POST':
        reason = request.POST.get('cancellation_reason')
        custom_reason = request.POST.get('custom_reason')
        
        if reason == 'custom':
            order_item.custom_cancellation_reason = custom_reason
        else:
            order_item.cancellation_reason = reason
        
        order_item.is_cancelled = True
        order_item.status = 'Cancelled'
        order_item.save()
        
        # Update product stock
        product_variant = order_item.product_variant
        product_variant.quantity += order_item.quantity
        product_variant.save()
        
        return JsonResponse({'status': 'success', 'message': 'Product has been cancelled successfully.'})
    
    cancellation_reasons = OrderItem.CANCELLATION_REASON_CHOICES
    return render(request, 'orders/cancellation_reason.html', {
        'order_item': order_item,
        'cancellation_reasons': cancellation_reasons
    })


@login_required(login_url='login_to_account')
def return_product(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    
    if request.method == 'POST':
        reason = request.POST.get('cancellation_reason')
        custom_reason = request.POST.get('custom_reason')
        
        if reason == 'custom':
            order_item.custom_cancellation_reason = custom_reason
        else:
            order_item.cancellation_reason = reason
        
        order_item.order.status = 'Returned'
        order_item.order.save()
        
        # Update product stock
        product_variant = order_item.product_variant
        product_variant.quantity += order_item.quantity
        product_variant.save()
        
        messages.success(request, 'Product return request has been submitted successfully.')
        return JsonResponse({'status': 'success', 'message': 'Product return request has been submitted successfully.'})
    
    cancellation_reasons = OrderItem.CANCELLATION_REASON_CHOICES
    return render(request, 'orders/cancellation_reason.html', {
        'order_item': order_item,
        'cancellation_reasons': cancellation_reasons
    })
