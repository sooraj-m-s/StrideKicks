from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.utils import timezone
import json
from .models import Category
from utils.decorators import admin_required


# Create your views here.


@admin_required
def category_list(request):
    first_name = request.user.first_name.title()
    categories = Category.objects.filter(is_deleted=False)
    data = {
        'first_name': first_name,
        'categories': categories,
    }
    return render(request, 'category.html', data)


@admin_required
def add_category(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            is_listed = data.get('is_listed', True)
            
            # Create new category
            category = Category(name=name, is_listed=is_listed)
            category.full_clean()  # This will run our custom validator
            category.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Category added successfully',
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'is_listed': category.is_listed
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


@admin_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, is_deleted=False)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            is_listed = data.get('is_listed', True)
            
            category.name = name
            category.is_listed = is_listed
            category.full_clean()  # This will run our custom validator
            category.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Category updated successfully',
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'is_listed': category.is_listed
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


@admin_required
def delete_category(request, category_id):
    if request.method == 'POST':
        try:
            category = get_object_or_404(Category, id=category_id, is_deleted=False)
            category.is_deleted = True
            category.deleted_at = timezone.now()
            category.save()
            return JsonResponse({
                'success': True,
                'message': 'Category deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)


@admin_required
def toggle_category_status(request, category_id):
    if request.method == 'POST':
        try:
            category = get_object_or_404(Category, id=category_id, is_deleted=False)
            category.is_listed = not category.is_listed
            category.save()
            return JsonResponse({
                'success': True,
                'message': f'Category {"listed" if category.is_listed else "unlisted"} successfully',
                'is_listed': category.is_listed
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
