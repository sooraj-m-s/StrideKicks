from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.db.models import Prefetch
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import uuid, time, logging, json, stripe
from django.views.decorators.http import require_POST
from django.conf import settings
from wallet.models import Wallet, WalletTransaction
from cart.models import Cart
from coupon.models import Coupon, UserCoupon
from userpanel.models import Address
from .models import Order, OrderItem, ReturnRequest
from .invoice_utils import generate_invoice_pdf


logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def checkout(request):
    try:
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

            if not address_id or not payment_method:
                messages.error(request, "Please select both address and payment method.")
                return redirect('checkout')

            address = Address.objects.get(id=address_id, user_id=request.user)

            with transaction.atomic():
                for item in cart.items.all():
                    if item.variant.is_deleted:
                        messages.error(request, f"{item.product.name} - {item.variant} is unavailable right now")
                        return redirect('view_cart')
                    elif item.quantity > item.variant.quantity:
                        messages.error(request, f"Not enough stock for {item.product.name} - {item.variant}")
                        return redirect('view_cart')

                subtotal = sum(item.price * item.quantity for item in cart.items.all())
                if payment_method == 'COD' and subtotal > 10000:
                    messages.error(request, 'COD not available on order above 10,000 rs.')
                    return redirect('checkout')
                amount_in_paise = int(total_amount * 100)

                if payment_method == 'WP':
                    user_id = request.user
                    wallet = Wallet.objects.get(user_id=user_id)
                    if not wallet.is_active:
                        messages.error(request, 'Your wallet is inactive. Please contact customer care.')
                        return redirect('checkout')
                    if wallet.balance < total_amount:
                        messages.error(request, 'Insufficient balance in your wallet. Please choose a different payment method.')
                        return redirect('checkout')
                if payment_method == 'ST':
                    payment_intent = stripe.PaymentIntent.create(
                        amount=amount_in_paise,
                        currency='inr',
                        metadata={
                            'order_id': str(order.id) if 'order' in locals() else None,
                            'user_id': str(request.user.user_id),
                        },
                        receipt_email=request.user.email,
                        automatic_payment_methods={'enabled': True},
                    )
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
                        payment_intent_id=payment_intent.id,
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
                    return render(request, 'stripe_checkout.html', {
                        'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
                        'client_secret': payment_intent.client_secret,
                        'order': order,
                        'amount': total_amount,
                    })

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
                    with transaction.atomic():
                        wallet = Wallet.objects.get(user_id=request.user)
                        wallet.balance -= total_amount
                        wallet.save()
                        WalletTransaction.objects.create(
                            wallet=wallet,
                            transaction_type="Dr",
                            amount=total_amount,
                            status="Completed",
                            transaction_id="TXN-" + str(int(time.time())) + uuid.uuid4().hex[:4].upper(),
                        )
                        order.items.update(item_payment_status='Paid')
                        order.payment_status = True
                        order.save()

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
    except Wallet.DoesNotExist:
        logger.error(f"Wallet not found for user: {request.user.user_id}")
        messages.error(request, 'Wallet not found. Please contact customer support.')
        return redirect('checkout')
    except ValueError as e:
        logger.error(f"ValueError in wallet payment processing: {e}")
        messages.error(request, f"An error occurred while processing your wallet payment.")
        return redirect('checkout')
    except Exception as e:
        logger.error(f"Error in checkout view: {e}")
        messages.error(request, "An unexpected error occurred during checkout. Please try again or contact support.")
        return redirect('view_cart')


@csrf_exempt
@require_POST
def stripe_callback(request):
    try:
        data = json.loads(request.body)
        payment_intent_id = data.get('payment_intent_id')
        order_id = data.get('order_id')
        order = Order.objects.get(id=order_id, user=request.user)
        order_items = OrderItem.objects.filter(order_id=order.id)
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if payment_intent.status == 'succeeded':
            order.payment_status = True
            order.payment_intent_id = payment_intent_id
            order.save()
            for item in order_items:
                item.item_payment_status = 'Paid'
                item.save()
            return JsonResponse({'success': True})
        else:
            order.payment_status = False
            order.save()
            return JsonResponse({'success': False, 'error': 'Payment not succeeded'})
    except Order.DoesNotExist:
        logger.error(f"Order not found: {order_id}")
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except OrderItem.DoesNotExist:
        logger.error(f"Order items not found for order: {order_id}")
        return JsonResponse({'success': False, 'error': 'Order items not found'}, status=404)
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred'}, status=400)


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_success.html', {'order': order})


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def my_orders(request):
    try:
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

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(orders, 5)
        try:
            orders = paginator.page(page)
        except PageNotAnInteger:
            orders = paginator.page(1)
        except EmptyPage:
            orders = paginator.page(paginator.num_pages)
        
        status_choices = OrderItem.STATUS_CHOICES
        data = {
            'orders': orders,
            'status_choices': status_choices,
            'search_query': search_query,
            'status_filter': status_filter,
        }
    except Exception as e:
        logger.error(f"Error in my_orders view: {e}")
        messages.error(request, "An error occurred while loading your orders. Please try again later.")
        data = {}
    return render(request, 'my_orders.html', data)


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('shipping_address').prefetch_related('items__product_variant__product__images'),
        id=order_id,
        user=request.user
    )
    return render(request, 'order_detail.html', {'order': order})


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def stripe_checkout(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.payment_status or (order.payment_method == 'ST' and order.payment_intent_id):
        messages.error(request, "This order has already been paid for.")
        return redirect('order_detail', order_id=order.id)

    amount_in_paise = int(order.total_amount * 100)  # Convert to paise
    try:
        if order.payment_intent_id:
            payment_intent = stripe.PaymentIntent.retrieve(order.payment_intent_id)
            if payment_intent.status in ['succeeded', 'requires_capture']:
                order.payment_status = True
                order.save()
                messages.success(request, "Payment already processed.")
                return redirect('order_detail', order_id=order.id)
            elif payment_intent.status == 'requires_payment_method':
                client_secret = payment_intent.client_secret
            else:
                payment_intent = stripe.PaymentIntent.create(
                    amount=amount_in_paise,
                    currency='inr',
                    metadata={
                        'order_id': order.id,
                        'user_id': request.user.user_id,
                    },
                    receipt_email=request.user.email,
                    automatic_payment_methods={'enabled': True},
                )
                order.payment_intent_id = payment_intent.id
                order.save()
                client_secret = payment_intent.client_secret
        else:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_in_paise,
                currency='inr',
                metadata={
                    'order_id': order.id,
                    'user_id': request.user.user_id,
                },
                receipt_email=request.user.email,
                automatic_payment_methods={'enabled': True},
            )
            order.payment_intent_id = payment_intent.id
            order.save()
            client_secret = payment_intent.client_secret

        data = {
            'order': order,
            'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
            'client_secret': client_secret,
            'amount': order.total_amount,
        }
        return render(request, 'stripe_checkout.html', data)
    except stripe.error.StripeError as e:
        logger.error(f"Error creating Stripe payment intent: {e}")
        messages.error(request, "Unable to create payment intent. Please try again.")
        return redirect('order_detail', order_id=order.id)
    except Exception as e:
        logger.error(f"Error in stripe checkout view: {e}")
        messages.error(request, "An unexpected error occurred. Please try again.")
        return redirect('order_detail', order_id=order.id)


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def cancel_product(request, item_id):
    try:
        order_item = OrderItem.objects.get(id=item_id, order__user=request.user)
        order = order_item.order
    except OrderItem.DoesNotExist:
        logger.error(f"Order item not found: {item_id}")
        messages.error(request, 'Order item not found.')
        return redirect('my_orders')
    
    if request.method == 'POST':
        reason = request.POST.get('cancellation_reason')
        custom_reason = request.POST.get('custom_reason')
        
        if reason == 'custom':
            order_item.custom_cancellation_reason = custom_reason
        else:
            order_item.cancellation_reason = reason

        # order status
        order_item.is_cancelled = True
        order_item.status = 'Cancelled'
        order_item.save()
        
        # qty
        product_variant = order_item.product_variant
        product_variant.quantity += order_item.quantity
        product_variant.save()

        # refund by proportion
        total_item_price = order_item.price * order_item.quantity
        proportion = total_item_price / (order.total_amount + order.discount)
        allocated_discount = order.discount * proportion
        returned_item_price = order_item.price  * order_item.quantity
        proportional_discount = (allocated_discount / order_item.quantity) * order_item.quantity
        refund_amount = returned_item_price - proportional_discount

        order.total_amount -= refund_amount
        order.subtotal -= order_item.original_price
        order.save()

        if order.payment_method in ['RP', 'WP']:
            if order_item.item_payment_status == 'Paid':
                wallet, _ = Wallet.objects.get_or_create(user=order.user)
                wallet.balance += refund_amount
                wallet.save()
                WalletTransaction.objects.create(
                                wallet=wallet,
                                transaction_type="Cr",
                                amount=refund_amount,
                                status="Completed",
                                transaction_id="TXN-" + str(int(time.time())) + uuid.uuid4().hex[:4].upper(),
                            )
        
        # payment status
        if order_item.item_payment_status == 'Paid':
            order_item.item_payment_status = 'Refunded'
        else:
            order_item.item_payment_status = 'Processing'
        order_item.save()
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
        
        order_item.status = 'Return_Requested'
        order_item.save()
        
        # Create a return request
        ReturnRequest.objects.create(order=order_item)
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

