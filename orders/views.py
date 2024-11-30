from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.db.models import Prefetch
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from decimal import Decimal
from django.conf import settings
from .razorpay_client import client
from .models import Order, OrderItem
from wallet.models import Wallet, WalletTransaction
from cart.models import Cart
from coupon.models import Coupon, UserCoupon
from userpanel.models import Address
import uuid, time
from .invoice_utils import generate_barcode, calculate_tax_details, generate_invoice_pdf


# Create your views here.


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        return redirect('view_cart')

    addresses = Address.objects.filter(user_id=request.user, is_deleted=False)
    coupon = request.session.get('coupon', {})
    coupon_id = coupon.get('coupon_id')
    discount_amount = Decimal(coupon.get('discount_amount', 0))
    coupon_code = None
    if coupon:
        coupon_code = Coupon.objects.get(id=coupon_id)
        total_price_after_coupon_discount = cart.total_price - discount_amount if discount_amount > 0 else cart.total_price
        total_amount = cart.total_price - discount_amount
    else:
        total_price_after_coupon_discount = cart.total_price
        total_amount = cart.total_price
    
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
            for item in cart.items.all():
                if item.quantity > item.variant.quantity:
                    messages.error(request, f"Not enough stock for {item.product.name} - {item.variant}")
                    return redirect('checkout')
            
            subtotal = sum(item.price * item.quantity for item in cart.items.all())
            if payment_method == 'COD' and subtotal > 10000:
                messages.error(request, 'COD not available on order above 10,000 rs.')
                return redirect('checkout')
            amount_in_paise = int(total_amount * 100)  # Convert to paise
            if payment_method == 'RP':
                try:
                    razorpay_order = client.order.create({
                        'amount': amount_in_paise,
                        'currency': 'INR',
                        'payment_capture': 1,
                        'notes': {
                            'shipping_address': f"{address.full_name}, {address.address}",
                            'contact': str(address.mobile_no)
                        }
                    })
                    razorpay_order_id = razorpay_order['id']
                except Exception as e:
                    messages.error(request, "Unable to create payment order. Please try again.")
                    return redirect('checkout')
            else:
                razorpay_order_id = None
            order = Order.objects.create(
                user=request.user,
                order_number=uuid.uuid4().hex[:12].upper(),
                coupon=coupon_code,
                discount=discount_amount,
                payment_method=payment_method,
                payment_status=False,
                subtotal=subtotal,
                total_amount=total_amount,
                shipping_address=address,
                shipping_cost=cart.delivery_charge or 0,
                razorpay_order_id=razorpay_order_id,
            )
            
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product_variant=item.variant,
                    quantity=item.quantity,
                    price=item.price,
                    item_payment_status='Unpaid',
                    original_price=item.variant.actual_price,
                )
                item.variant.quantity -= item.quantity
                item.variant.save()
            if coupon_code:
                UserCoupon.objects.create(
                    user=request.user,
                    coupon=coupon_code,
                    order=order,
                )
            cart.delete()
            if 'coupon' in request.session:
                del request.session['coupon']
                request.session.modified = True
            
            if payment_method == 'WP':
                try:
                    with transaction.atomic():
                        try:
                            user_id = request.user
                            if not user_id:
                                raise ValueError('Wallet not found')
                            wallet = Wallet.objects.get(user_id=user_id)
                            if not wallet.is_active:
                                raise ValueError('Wallet is inactive, please contact customer care.')
                        except Wallet.DoesNotExist:
                            raise ValueError('Wallet not created.')
                        except ValueError as e:
                            raise ValueError(str(e))
                        if wallet.balance < total_amount:
                            raise ValueError("Insufficient balance in wallet.")
                        
                        wallet.balance -= total_amount
                        wallet.save()
                        WalletTransaction.objects.create(
                            wallet=wallet,
                            transaction_type="Dr",
                            amount=total_amount,
                            status="Completed",
                            transaction_id="TXN-" + str(int(time.time())) + uuid.uuid4().hex[:4].upper(),
                        )
                        for order_item in order.orderitem_set.all():
                            order_item.item_payment_status = 'paid'
                            order_item.save()
                except ValueError as e:
                    messages.error(request, str(e))
                    return redirect('checkout')
                except Exception as e:
                    messages.error(request, "An error occurred while processing your payment. Please try again.")
                    return redirect('checkout')
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

    total_discount = cart.get_total_actual_price() - cart.total_price
    data = {
        'cart': cart,
        'addresses': addresses,
        'total_amount': total_amount,
        'total_discount': total_discount,
        'payment_methods': Order.PAYMENT_METHOD_CHOICES,
        'coupon_code': coupon_code,
        'discount_amount': discount_amount,
        'total_price_after_coupon_discount': total_price_after_coupon_discount,
    }
    return render(request, 'checkout.html', data)


@csrf_exempt
def razorpay_callback(request):
    if request.method == "POST":
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
            order_items = OrderItem.objects.filter(order_id=order.id)
        except Order.DoesNotExist:
            return HttpResponse("404 Not Found", status=404)

        try:
            client.utility.verify_payment_signature(params_dict)
        except:
            return render(request, 'ckeckout.html')

        order.razorpay_payment_id = payment_id
        order.razorpay_signature = signature
        order.payment_status = True
        order.save()
        for item in order_items:
            item.item_payment_status = 'Paid'
            item.save()

        return redirect('order_success', order_id=order.id)
    return HttpResponse("Invalid Request", status=400)


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
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

    return render(request, 'my_orders.html', data)


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_detail.html', {'order': order})


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def cancel_product(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    order = order_item.order
    
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
        
        product_variant = order_item.product_variant
        product_variant.quantity += order_item.quantity
        product_variant.save()

        # refund by proportion
        discount_deduction = (order_item.price / order.total_amount) * order.discount
        refund = order_item.price - discount_deduction
        order.total_amount -= refund
        order.subtotal -= order_item.original_price

        if order.payment_method in ['RP', 'WP'] or (order.payment_method == 'COD' and order_item.status == 'Delivered'):
            if order_item.item_payment_status == 'Paid':
                wallet, _ = Wallet.objects.get_or_create(user=order.user)
                wallet.balance += refund
                wallet.save()
                WalletTransaction.objects.create(
                                wallet=wallet,
                                transaction_type="Cr",
                                amount=refund,
                                status="Completed",
                                transaction_id="TXN-" + str(int(time.time())) + uuid.uuid4().hex[:4].upper(),
                            )
            return JsonResponse({'status': 'success', 'message': 'Product successfully cancelled and the amount credited to your wallet.'})
        return JsonResponse({'status': 'success', 'message': 'Product has been cancelled successfully.'})
    
    cancellation_reasons = OrderItem.CANCELLATION_REASON_CHOICES
    return render(request, 'cancellation_reason.html', {
        'order_item': order_item,
        'cancellation_reasons': cancellation_reasons
    })


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
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
        
        product_variant = order_item.product_variant
        product_variant.quantity += order_item.quantity
        product_variant.save()
        
        messages.success(request, 'Product return request has been submitted successfully.')
        return JsonResponse({'status': 'success', 'message': 'Product return request has been submitted successfully.'})
    
    cancellation_reasons = OrderItem.CANCELLATION_REASON_CHOICES
    return render(request, 'cancellation_reason.html', {
        'order_item': order_item,
        'cancellation_reasons': cancellation_reasons
    })


@login_required
def download_invoice(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    if order_item.status != 'Delivered':
        return HttpResponse("Invoice not available for this item", status=400)
    if not order_item.invoice_number:
        order_item.save()
    
    pdf = generate_invoice_pdf(order_item)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order_item.invoice_number}.pdf"'
    return response
