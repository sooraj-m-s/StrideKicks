from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
import json
from utils.decorators import admin_required
from .models import Coupon, UserCoupon


# Create your views here.


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def coupon_list(request):
    first_name = request.user.first_name.title()
    coupons = Coupon.objects.all().order_by('-created_at')
    data = {
        'first_name': first_name,
        'coupons': coupons,
    }
    return render(request, 'coupon_management.html', data)


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_coupon(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '').strip().upper()
            discount_type = data.get('discount_type')
            discount_value = data.get('discount_value')
            min_cart_value = data.get('min_cart_value')
            max_discount = data.get('max_discount')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            max_usage = data.get('max_usage', 1)
            max_usage_per_user = data.get('max_usage_per_user', 1)
            description = data.get('description', '').strip()
            active = data.get('active', True)

            if Coupon.objects.filter(code__exact=code).exists():
                raise ValidationError("A coupon with this code already exists.")

            coupon = Coupon(
                code=code,
                discount_type=discount_type,
                discount_value=discount_value,
                min_cart_value=min_cart_value,
                max_discount=max_discount,
                start_date=start_date,
                end_date=end_date,
                max_usage=max_usage,
                max_usage_per_user=max_usage_per_user,
                description=description,
                active=active
            )
            coupon.full_clean()
            coupon.save()
            
            return JsonResponse({
                'success': True, 'message': 'Coupon added successfully',
                'coupon': {
                    'id': coupon.id,
                    'code': coupon.code,
                    'discount_type': coupon.discount_type,
                    'discount_value': str(coupon.discount_value),
                    'active': coupon.active
                }
            })
        except ValidationError as e:
            return JsonResponse({'success': False, 'message': e.messages[0]}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'GET':
        # Return the coupon data for editing
        return JsonResponse({
            'success': True,
            'coupon': {
                'id': coupon.id,
                'code': coupon.code,
                'discount_type': coupon.discount_type,
                'discount_value': str(coupon.discount_value),
                'min_cart_value': str(coupon.min_cart_value) if coupon.min_cart_value else None,
                'max_discount': str(coupon.max_discount) if coupon.max_discount else None,
                'start_date': coupon.start_date.isoformat() if coupon.start_date else None,
                'end_date': coupon.end_date.isoformat() if coupon.end_date else None,
                'max_usage': coupon.max_usage,
                'max_usage_per_user': coupon.max_usage_per_user,
                'description': coupon.description,
                'active': coupon.active
            }
        })
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '').strip().upper()
            
            # Check if another coupon exists with the same code
            if Coupon.objects.filter(code__exact=code).exclude(id=coupon_id).exists():
                raise ValidationError("A coupon with this code already exists.")
            
            coupon.code = code
            coupon.discount_type = data.get('discount_type')
            coupon.discount_value = data.get('discount_value')
            coupon.min_cart_value = data.get('min_cart_value')
            coupon.max_discount = data.get('max_discount')
            coupon.start_date = data.get('start_date')
            coupon.end_date = data.get('end_date')
            coupon.max_usage = data.get('max_usage', 1)
            coupon.max_usage_per_user = data.get('max_usage_per_user', 1)
            coupon.description = data.get('description', '').strip()
            active = data.get('active')
            if active is not None:
                coupon.active = active in [True, 'true', 'True', 1, '1']
            
            coupon.full_clean()
            coupon.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Coupon updated successfully',
                'coupon': {
                    'id': coupon.id,
                    'code': coupon.code,
                    'discount_type': coupon.discount_type,
                    'discount_value': str(coupon.discount_value),
                    'active': coupon.active
                }
            })
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': e.messages[0]
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    else:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method'
        }, status=405)


@login_required
@admin_required
def delete_coupon(request, coupon_id):
    if request.method == 'POST':
        try:
            coupon = get_object_or_404(Coupon, id=coupon_id)
            # Check if the coupon has been used
            if UserCoupon.objects.filter(coupon=coupon).exists():
                coupon.active = False
                coupon.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Coupon has been deactivated as it was already used'
                })
            else:
                coupon.delete()
                return JsonResponse({
                    'success': True,
                    'message': 'Coupon deleted successfully'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def toggle_coupon_status(request, coupon_id):
    if request.method == 'POST':
        try:
            coupon = get_object_or_404(Coupon, id=coupon_id)
            coupon.active = not coupon.active
            coupon.save()
            return JsonResponse({
                'success': True,
                'message': f'Coupon {"activated" if coupon.active else "deactivated"} successfully',
                'active': coupon.active
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
