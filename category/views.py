from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.core.exceptions import ValidationError
from django.utils import timezone
import json
from .models import Category
from utils.decorators import admin_required


# Create your views here.


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def category_list(request):
    first_name = request.user.first_name.title()
    categories = Category.objects.filter(is_deleted=False)
    data = {
        'first_name': first_name,
        'categories': categories,
    }
    return render(request, 'category.html', data)


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_category(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            is_listed = data.get('is_listed', True)

            if Category.objects.filter(name__iexact=name, is_deleted=False).exists():
                raise ValidationError("A category with this exact name already exists.")
            
            category = Category(name=name, is_listed=is_listed)
            category.full_clean()
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
            return JsonResponse({'success': False, 'message': e.messages[0]}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, is_deleted=False)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            is_listed = data.get('is_listed', True)

            if Category.objects.filter(name__exact=name, is_deleted=False).exists():
                raise ValidationError("A category with this exact name already exists.")
            
            category.name = name
            category.is_listed = is_listed
            category.full_clean()
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
            return JsonResponse({'success': False, 'message': e.messages[0]}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_category(request, category_id):
    if request.method == 'POST':
        try:
            category = get_object_or_404(Category, id=category_id, is_deleted=False)
            category.is_deleted = True
            category.deleted_at = timezone.now()
            category.save()
            return JsonResponse({'success': True, 'message': 'Category deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
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
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
