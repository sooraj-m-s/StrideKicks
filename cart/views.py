from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from .models import Cart, CartItem
from coupon.models import Coupon, UserCoupon
from product.models import Product, ProductVariant


# Create your views here.


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_total = sum(item.total_price for item in cart.items.all())
    delivery_charge = 0 if cart_total > 4999 else 99
    cart.total_price = cart_total + delivery_charge
    cart.delivery_charge = delivery_charge
    cart.save()

    total_discount = cart.get_total_actual_price() - cart.total_price
    latest_products = Product.objects.filter(is_deleted=False).order_by('-created_at')[:5]
    total_actual_price = cart.get_total_actual_price()

    coupon = request.session.get('coupon', {})
    coupon_id = coupon.get('coupon_id')
    discount_amount = Decimal(coupon.get('discount_amount', '0'))
    coupon_code = None
    if coupon:
        coupon_code = Coupon.objects.get(id=coupon_id)
    total_price_after_coupon_discount = cart.total_price - int(discount_amount) if int(discount_amount) > 0 else cart.total_price
    data = {
        'cart': cart,
        'total_discount': total_discount,
        'latest_products': latest_products,
        'max_quantity': 5,
        'total_actual_price': total_actual_price,
        'coupon_code': coupon_code,
        'discount_amount': discount_amount,
        'total_price_after_coupon_discount': total_price_after_coupon_discount
    }
    return render(request, 'cart.html', data)


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def update_cart_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        max_quantity = min(5, cart_item.variant.quantity)
        if quantity <= max_quantity:
            cart_item.quantity = quantity
            cart_item.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'total_price': float(cart_item.cart.total_price),
                'item_total': float(cart_item.total_price)
            })
    
    return redirect('view_cart')


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        
        coupon_data = request.session.get('coupon')
        if coupon_data:
            del request.session['coupon']
            request.session.modified = True
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'cart_total': float(cart_item.cart.total_price)})
    
    return redirect('view_cart')


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        variant_id = request.POST.get('variant')
        quantity = 1
        
        cart, created = Cart.objects.get_or_create(user=request.user)
        variant = get_object_or_404(ProductVariant, id=variant_id) if variant_id else None
        
        try:
            if variant and variant.sale_price:
                discount = (variant.actual_price - variant.sale_price) * quantity
            else:
                discount = 0
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                variant=variant,
                defaults={
                    'quantity': 0,
                    'price': variant.sale_price if variant else product.price,
                    'discount': discount
                }
            )
            
            new_quantity = cart_item.quantity + quantity
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, 'Product added to cart successfully')
            
        except ValidationError as e:
            messages.error(request, str(e))
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Product added to cart successfully',
                'cart_total': float(cart.total_price)
            })
    
    return redirect('view_cart')


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def available_coupons(request):
    if request.method == 'GET':
        coupons = Coupon.objects.filter(active=True, is_deleted=False)
        coupon_list = [{'code': coupon.code, 'description': coupon.description} for coupon in coupons]
        return JsonResponse({'coupons': coupon_list})
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def apply_coupon(request, coupon_code):
    if request.method == 'POST':
        try:
            coupon = get_object_or_404(Coupon, code=coupon_code)
            cart = Cart.objects.get(user=request.user)
            
            if UserCoupon.objects.filter(user=request.user, coupon=coupon).exists():
                return JsonResponse({'success': False, 'message': 'You have already used this coupon'})
            if UserCoupon.objects.filter(coupon=coupon).count() >= coupon.max_usage:
                return JsonResponse({'success': False, 'message': 'Coupon usage limit reached'})
            if coupon.end_date > timezone.now():
                return JsonResponse({'success': False, 'message': 'Coupon has expired'})
            if not coupon.active:
                return JsonResponse({'success': False, 'message': 'Coupon is inactive'})
            if cart.total_price < coupon.min_cart_value:
                return JsonResponse({'success': False, 'message': f'Minimum cart value of ₹{coupon.min_cart_value} required to apply this coupon.'})
            if coupon.discount_type == 'fixed':
                discount = float(coupon.discount_value)
            else:
                discount = float(cart.total_price * coupon.discount_value / 100)
                if coupon.max_discount:
                    discount = min(discount, float(coupon.max_discount))
            
            request.session['coupon'] = {
                'coupon_id': coupon.id,
                'discount_amount': discount,
            }
            return JsonResponse({
                'success': True,
                'message': 'Coupon applied successfully!',
                'discount_amount': str(discount),
                'new_total': cart.total_price - Decimal(discount),
                'coupon_code': coupon.code
            })
        
        except Exception as e:
            return JsonResponse({'success': False, 'message': f"An unexpected error occurred: {str(e)}"})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def remove_coupon(request):
    if request.method == 'POST':
        try:
            cart = Cart.objects.get(user=request.user)
            coupon_data = request.session.get('coupon')
            
            if coupon_data:
                del request.session['coupon']
                request.session.modified = True
                
                return JsonResponse({'success': True, 'message': 'Coupon removed successfully', 'new_total': float(cart.total_price)})
            else:
                return JsonResponse({'success': False, 'message': 'No coupon applied to remove'})
        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Cart not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
