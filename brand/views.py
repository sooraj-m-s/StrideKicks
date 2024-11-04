from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from .models import Brand
import json

# Create your views here.


@login_required
def brand_list(request):
    brands = Brand.objects.filter(is_deleted=False)
    return render(request, 'brand.html', {'brands': brands})

@login_required
def add_brand(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            is_listed = data.get('is_listed', True)
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
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

@login_required
def edit_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id, is_deleted=False)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            is_listed = data.get('is_listed', True)
            
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
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

@login_required
def delete_brand(request, brand_id):
    if request.method == 'POST':
        try:
            brand = get_object_or_404(Brand, id=brand_id, is_deleted=False)
            brand.soft_delete()
            return JsonResponse({
                'success': True,
                'message': 'Brand deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

@login_required
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
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
