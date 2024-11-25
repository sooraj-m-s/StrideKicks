from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.views.decorators.cache import cache_control
import json
from .models import Brand
from utils.decorators import admin_required


# Create your views here.


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def brand_list(request):
    first_name = request.user.first_name.title()
    brands = Brand.objects.filter(is_deleted=False)
    brand = {
        'first_name': first_name,
        'brands': brands,
    }
    return render(request, 'brand.html', brand)


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_brand(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            is_listed = data.get('is_listed', True)

            if Brand.objects.filter(name__iexact=name, is_deleted=False).exists():
                raise ValidationError("A brand with this exact name already exists.")

            brand = Brand(name=name, is_listed=is_listed)
            brand.full_clean()
            brand.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Brand added successfully',
                'brand': {
                    'id': brand.id,
                    'name': brand.name,
                    'is_listed': brand.is_listed
                }
            })
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': e.messages[0]
            }, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def edit_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id, is_deleted=False)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            is_listed = data.get('is_listed', True)

            if Brand.objects.filter(name__exact=name, is_deleted=False).exists():
                raise ValidationError("A brand with this exact name already exists.")
            
            brand.name = name
            brand.is_listed = is_listed
            brand.full_clean()
            brand.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Brand updated successfully',
                'brand': {
                    'id': brand.id,
                    'name': brand.name,
                    'is_listed': brand.is_listed
                }
            })
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': e.messages[0]
            }, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@admin_required
def delete_brand(request, brand_id):
    if request.method == 'POST':
        try:
            brand = get_object_or_404(Brand, id=brand_id, is_deleted=False)
            brand.soft_delete()
            return JsonResponse({'success': True, 'message': 'Brand deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def toggle_brand_status(request, brand_id):
    if request.method == 'POST':
        try:
            brand = get_object_or_404(Brand, id=brand_id, is_deleted=False)
            brand.is_listed = not brand.is_listed
            brand.save()
            return JsonResponse({
                'success': True,
                'message': f'Brand {"listed" if brand.is_listed else "unlisted"} successfully',
                'is_listed': brand.is_listed
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
