from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.http import JsonResponse
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
import json, logging
from coupon.models import Coupon, UserCoupon
from product.models import Product, ProductVariant
from .models import Cart, CartItem


logger = logging.getLogger(__name__)

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def view_cart(request):
    try:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.all().select_related('product', 'variant')
        
        # Calculate totals
        total_actual_price = sum(item.variant.actual_price * item.quantity for item in cart_items)
        total_sale_price = sum(item.variant.sale_price * item.quantity for item in cart_items)
        total_normal_discount = total_actual_price - total_sale_price
        total_offer_discount = sum(item.get_offer_discount() for item in cart_items)
        
        # Calculate final total after all discounts
        total_after_discounts = total_sale_price - total_offer_discount
        
        # Apply delivery charge
        delivery_charge = 0 if total_after_discounts > 4999 else 99
        final_total = total_after_discounts + delivery_charge
        
        # Update cart
        cart.total_price = final_total
        cart.delivery_charge = delivery_charge
        cart.save()

        # Get coupon if any
        coupon = request.session.get('coupon', {})
        coupon_id = coupon.get('coupon_id')
        discount_amount = Decimal(coupon.get('discount_amount', '0'))
        coupon_code = None
        if coupon:
            try:
                coupon_code = Coupon.objects.get(id=coupon_id, is_deleted=False, active=True)
            except Coupon.DoesNotExist:
                logger.warning(f"Coupon with ID {coupon_id} not found or inactive.")
                messages.error(request, 'The coupon you applied earlier is no longer available. It has been removed from your cart.')
                del request.session['coupon']
                return redirect('view_cart')

        # Final total after coupon
        total_after_coupon = final_total - discount_amount if discount_amount > 0 else final_total

        # Check if any cart item quantity exceeds available stock
        cart_exceeds_stock = False
        for item in cart_items:
            if item.quantity > item.variant.quantity:
                cart_exceeds_stock = True
                break

        data = {
            'cart': cart,
            'cart_items': cart_items,
            'total_actual_price': total_actual_price,
            'total_normal_discount': total_normal_discount,
            'total_offer_discount': total_offer_discount,
            'delivery_charge': delivery_charge,
            'coupon_code': coupon_code,
            'discount_amount': discount_amount,
            'total_after_coupon': total_after_coupon,
            'latest_products': Product.objects.filter(is_deleted=False).order_by('-created_at')[:5],
            'max_quantity': 5,
            'cart_exceeds_stock': cart_exceeds_stock,
        }

        return render(request, 'cart.html', data)
    except Cart.DoesNotExist:
        logger.error(f"Cart does not exist for user {request.user.id}")
        messages.error(request, 'Your cart is empty.')
        return redirect('view_cart')
    except Exception as e:
        logger.error(f"Error in view_cart: {e}")
        messages.error(request, 'An error occurred while loading the cart.')
        return redirect('view_cart')


@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
            
            if quantity < 1 or quantity > 5:
                return JsonResponse({'success': False, 'message': 'Quantity must be between 1 and 5'})
            
            # Only check stock if trying to increase quantity
            if quantity > cart_item.quantity and quantity > cart_item.variant.quantity:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {cart_item.variant.quantity} items available in stock'
                })
            
            # Update quantity
            cart_item.quantity = quantity
            cart_item.save()
            
            # Get cart totals
            cart = cart_item.cart
            cart_items = cart.items.all()
            
            # Calculate totals
            total_actual_price = sum(item.variant.actual_price * item.quantity for item in cart_items)
            total_sale_price = sum(item.variant.sale_price * item.quantity for item in cart_items)
            total_normal_discount = total_actual_price - total_sale_price
            total_offer_discount = sum(item.get_offer_discount() for item in cart_items)
            
            # Calculate final total after all discounts
            total_after_discounts = total_sale_price - total_offer_discount
            
            # Apply delivery charge
            delivery_charge = 0 if total_after_discounts > 4999 else 99
            final_total = total_after_discounts + delivery_charge
            
            # Update cart
            cart.total_price = final_total
            cart.delivery_charge = delivery_charge
            cart.save()

            # Get coupon if any
            coupon = request.session.get('coupon', {})
            discount_amount = Decimal(coupon.get('discount_amount', '0'))
            total_after_coupon = final_total - discount_amount if discount_amount > 0 else final_total

            # Get item specific totals
            item_sale_total = cart_item.variant.sale_price * cart_item.quantity
            item_offer_discount = cart_item.get_offer_discount()
            item_final_price = cart_item.get_final_price()
            
            return JsonResponse({
                'success': True,
                'total_actual_price': float(total_actual_price),
                'total_normal_discount': float(total_normal_discount),
                'total_offer_discount': float(total_offer_discount),
                'total_after_discounts': float(total_after_discounts),
                'delivery_charge': delivery_charge,
                'total_after_coupon': float(total_after_coupon),
                'item_sale_total': float(item_sale_total),
                'item_offer_discount': float(item_offer_discount),
                'item_final_price': float(item_final_price),
                'items_count': cart.items.count(),
                'is_free_delivery': total_after_discounts > 4999
            })
            
        except CartItem.DoesNotExist:
            logger.error(f"Cart item with ID {item_id} not found for user {request.user.id}")
            return JsonResponse({'success': False, 'message': 'Cart item not found'})
        except (ValueError, json.JSONDecodeError):
            logger.error(f"Invalid quantity value for cart item with ID {item_id} for user {request.user.id}")
            return JsonResponse({'success': False, 'message': 'Invalid quantity value'})
        except Exception as e:
            logger.error(f"Error in update_cart_item: {e}")
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def remove_from_cart(request, item_id):
    try:
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
    except CartItem.DoesNotExist:
        logger.error(f"Cart item with ID {item_id} not found for user {request.user.id}")
        messages.error(request, 'Cart item not found')
        return redirect('view_cart')
    except Exception as e:
        logger.error(f"Error in remove_from_cart: {e}")
        messages.error(request, str(e))
        return redirect('view_cart')


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        variant_id = request.POST.get('variant')
        quantity = 1
        
        cart, _ = Cart.objects.get_or_create(user=request.user)
        variant = get_object_or_404(ProductVariant, id=variant_id) if variant_id else None
        
        try:
            # Check if variant exists and has stock
            if not variant or variant.quantity < 1:
                messages.error(request, 'This product is out of stock')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Out of stock'})
                return redirect('product_detail', product_id=product_id)
            
            if variant and variant.sale_price:
                discount = (variant.actual_price - variant.sale_price) * quantity
            else:
                discount = 0
            
            cart_item, _ = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                variant=variant,
                defaults={
                    'quantity': 0,
                    'price': variant.sale_price if variant else product.price,
                    'discount': discount
                }
            )
            
            # Check if adding quantity exceeds stock
            new_quantity = cart_item.quantity + quantity
            if new_quantity > variant.quantity:
                messages.error(request, f'Only {variant.quantity} items available in stock')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': f'Only {variant.quantity} items available in stock'})
                return redirect('product_detail', product_id=product_id)
            
            # Check if adding quantity exceeds maximum limit
            if new_quantity > 5:
                messages.error(request, 'Maximum quantity limit is 5')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Maximum quantity limit is 5'})
                return redirect('product_detail', product_id=product_id)
            
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, 'Product added to cart successfully')
            
        except ValidationError as e:
            logger.error(f"Validation error in add_to_cart: {e}")
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
    try:
        if request.method == 'GET':
            coupons = Coupon.objects.filter(active=True, is_deleted=False)
            coupon_list = [{'code': coupon.code, 'description': coupon.description} for coupon in coupons]
            return JsonResponse({'coupons': coupon_list})
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
    except Exception as e:
        logger.error(f"Error in available_coupons: {e}")
        return JsonResponse({'success': False, 'message': 'An unexpected error occurred'})


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def apply_coupon(request, coupon_code):
    if request.method == 'POST':
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            cart = Cart.objects.get(user=request.user)
            
            if UserCoupon.objects.filter(user=request.user, coupon=coupon).exists():
                return JsonResponse({'success': False, 'message': 'You have already used this coupon'})
            if UserCoupon.objects.filter(coupon=coupon).count() >= coupon.max_usage:
                return JsonResponse({'success': False, 'message': 'Coupon usage limit reached'})
            if coupon.end_date < timezone.now():
                return JsonResponse({'success': False, 'message': 'Coupon has expired'})
            if not coupon.active:
                return JsonResponse({'success': False, 'message': 'Coupon is inactive'})
            if cart.total_price < coupon.min_cart_value:
                return JsonResponse({'success': False, 'message': f'Minimum cart value of ₹{coupon.min_cart_value} required to apply this coupon.'})
            
            if cart.total_price < 5000:
                effective_price = cart.total_price - 99
            else:
                effective_price = cart.total_price
            if coupon.discount_type == 'fixed':
                discount = float(coupon.discount_value)
            else:
                discount = float(effective_price * coupon.discount_value // 100)
                if coupon.max_discount:
                    discount = max(discount, float(coupon.max_discount))
            
            if discount > effective_price - 1:
                return JsonResponse({'success': False, 'message': 'Coupon discount exceeds cart total'})
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
        
        except ObjectDoesNotExist:
            logger.error(f"Invalid coupon code: {coupon_code}")
            return JsonResponse({'success': False, 'message': 'Invalid coupon, please enter a valid coupon code'})
        except Exception as e:
            logger.error(f"Error in apply_coupon: {e}")
            return JsonResponse({'success': False, 'message': "An unexpected error occurred"})
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
            logger.error(f"Cart not found for user: {request.user.id}")
            return JsonResponse({'success': False, 'message': 'Cart not found'})
        except Exception as e:
            logger.error(f"Error in remove_coupon: {e}")
            return JsonResponse({'success': False, 'message': 'An error occurred while removing the coupon'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

