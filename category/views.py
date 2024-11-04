from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from .models import Category
from django.utils import timezone
import json


# Create your views here.


@login_required
def category_list(request):
    categories = Category.objects.filter(is_deleted=False)
    return render(request, 'category.html', {'categories': categories})

@login_required
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

@login_required
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

@login_required
def delete_category(request, category_id):
    if request.method == 'POST':
        try:
            category = get_object_or_404(Category, id=category_id, is_deleted=False)
            category.soft_delete()
            return JsonResponse({
                'success': True,
                'message': 'Category deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

@login_required
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
