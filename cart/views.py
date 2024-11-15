from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db.models import Sum
from .models import Cart, CartItem
from product.models import Product, ProductVariant


# Create your views here.


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    # Calculate total price of items
    cart_total = sum(item.total_price for item in cart.items.all())
    
    # Calculate delivery charge
    delivery_charge = 0 if cart_total > 4999 else 99
    
    # Update cart
    cart.total_price = cart_total + delivery_charge
    cart.delivery_charge = delivery_charge
    cart.save()

    total_discount = cart.items.aggregate(total_discount=Sum('discount'))['total_discount'] or 0
    latest_products = Product.objects.filter(is_deleted=False).order_by('-created_at')[:5]
    total_actual_price = cart.get_total_actual_price()
    data = {
        'cart': cart,
        'total_discount': total_discount,
        'latest_products': latest_products,
        'max_quantity': 5,
        'total_actual_price': total_actual_price,
    }
    return render(request, 'cart.html', data)


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def update_cart_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        # Validate quantity against stock
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


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_total': float(cart_item.cart.total_price)
            })
    
    return redirect('view_cart')


@login_required(login_url='login_to_account')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        variant_id = request.POST.get('variant')
        quantity = 1  # Default quantity
        
        # Get or create cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        variant = get_object_or_404(ProductVariant, id=variant_id) if variant_id else None
        
        try:
            # Calculate discount
            if variant and variant.sale_price:
                discount = (variant.actual_price - variant.sale_price) * quantity
            else:
                discount = 0
            
            # Get or create cart item
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
            
            # Update quantity
            new_quantity = cart_item.quantity + quantity
            cart_item.quantity = new_quantity
            cart_item.save()  # This will trigger validation in the model

            # Recalculate discount based on new quantity
            # if variant and variant.sale_price:
            #     cart_item.discount = (variant.actual_price - variant.sale_price) * new_quantity
            # else:
            #     cart_item.discount = 0
            # cart_item.save()
            
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
