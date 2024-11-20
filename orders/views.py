from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.db.models import Prefetch
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
from .razorpay_client import client
from .models import Order, OrderItem
from cart.models import Cart
from userpanel.models import Address
import uuid

import logging
logger = logging.getLogger(__name__)
# Create your views here.


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        return redirect('view_cart')

    addresses = Address.objects.filter(user_id=request.user, is_deleted=False)
    
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method')

        if payment_method == 'CC' or payment_method == 'PP' or payment_method == 'BT':
            messages.error(request, "Current payment method is not available. Please try another payment method.")
            return redirect('checkout')
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
            total_amount = cart.total_price
            amount_in_paise = int(total_amount * 100)  # Convert to paise
            # Create Razorpay order
            if payment_method == 'RP':  # Razorpay
                logger.info(f"Attempting to create Razorpay order for amount: {amount_in_paise}")
                try:
                    
                    logger.info(f"Creating Razorpay order for amount: {amount_in_paise} paise")
                    razorpay_order = client.order.create({
                        'amount': amount_in_paise,
                        'currency': 'INR',
                        'payment_capture': 1,
                        'notes': {
                            'shipping_address': f"{address.full_name}, {address.address}",
                            'contact': str(address.mobile_no)
                        }
                    })
                    logger.info(f"Razorpay order created successfully: {razorpay_order['id']}")
                    razorpay_order_id = razorpay_order['id']
                except Exception as e:
                    logger.error(f"Error creating Razorpay order: {str(e)}")
                    messages.error(request, "Unable to create payment order. Please try again.")
                    return redirect('checkout')
            else:
                razorpay_order_id = None
            
            # Create order
            order = Order.objects.create(
                user=request.user,
                order_number=uuid.uuid4().hex[:12].upper(),
                payment_method=payment_method,
                payment_status=False,
                subtotal=subtotal,
                total_amount=total_amount,
                shipping_address=address,
                shipping_cost=cart.delivery_charge or 0,
                razorpay_order_id=razorpay_order_id,
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
            
            if payment_method == 'RP':
                context = {
                    'order': order,
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                    'callback_url': request.build_absolute_uri(reverse('razorpay_callback')),
                    'amount': amount_in_paise,
                }
                return render(request, 'razorpay_checkout.html', context)
            else:
                messages.success(request, f"Order placed successfully. Your order number is {order.order_number}")
                return redirect('order_success', order_id=order.id)

    context = {
        'cart': cart,
        'addresses': addresses,
        'payment_methods': Order.PAYMENT_METHOD_CHOICES,
    }
    return render(request, 'checkout.html', context)


@csrf_exempt
def razorpay_callback(request):
    if request.method == "POST":
        logger.info("Received Razorpay callback")
        logger.info(f"POST data: {request.POST}")
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)
        except Order.DoesNotExist:
            return HttpResponse("404 Not Found", status=404)

        # Verify the payment signature
        try:
            client.utility.verify_payment_signature(params_dict)
        except:
            return render(request, 'payment_fail.html')

        order.razorpay_payment_id = payment_id
        order.razorpay_signature = signature
        order.payment_status = True
        order.save()

        return redirect('order_success', order_id=order.id)
    return HttpResponse("Invalid Request", status=400)


@login_required
def order_success(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    return render(request, 'order_success.html', {'order': order})


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def my_orders(request):
    orders = Order.objects.filter(user=request.user)
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    if search_query:
        orders = orders.filter(order_number__istartswith=search_query)

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


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def cancel_product(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    
    if request.method == 'POST':
        reason = request.POST.get('cancellation_reason')
        custom_reason = request.POST.get('custom_reason')
        
        if reason == 'custom':
            order_item.custom_cancellation_reason = custom_reason
        else:
            order_item.cancellation_reason = reason
        
        # order = Order.objects.get(id=order_item.order_id)
        # order.total_amount -= order_item.price
        # order.save()

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


@login_required
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
