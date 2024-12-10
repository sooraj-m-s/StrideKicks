from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import cache_control
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Wallet, WalletTransaction, Offer
from product.models import Product
from category.models import Category
from utils.decorators import admin_required


# Create your views here.


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def wallet_view(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')[:10]
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(transactions, 5)
    try:
        transactions = paginator.page(page)
    except PageNotAnInteger:
        transactions = paginator.page(1)
    except EmptyPage:
        transactions = paginator.page(paginator.num_pages)

    context = {
        'wallet': wallet,
        'transactions': transactions,
    }
    return render(request, 'wallet.html', context)


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def offer_management(request):
    search_query = request.GET.get('search', '')
    offers = Offer.objects.filter(
        Q(name__icontains=search_query) |
        Q(offer_type__icontains=search_query)
    ).order_by('-created_at')

    context = {
        'offers': offers,
        'search_query': search_query,
        'offer_types': Offer.OFFER_TYPES,
        'first_name': request.user.first_name,
    }
    return render(request, 'offers.html', context)


@login_required
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_offer(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        offer_type = request.POST.get('offer_type')
        discount_percentage = request.POST.get('discount_percentage')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        try:
            offer = Offer(
                name=name,
                description=description,
                offer_type=offer_type,
                discount_percentage=int(discount_percentage),
                start_date=start_date,
                end_date=end_date
            )
            
            # Set product or category based on offer type
            if offer_type == 'Product':
                product_id = request.POST.get('product')
                if not product_id:
                    return JsonResponse({'success': False, 'message': 'Please select a product'})
                offer.product = get_object_or_404(Product, id=product_id)
            else:  # Category offer
                category_id = request.POST.get('category')
                if not category_id:
                    return JsonResponse({'success': False, 'message': 'Please select a category'})
                offer.category = get_object_or_404(Category, id=category_id)
            offer.save()
            return JsonResponse({'success': True, 'message': 'Offer added successfully!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    products = Product.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'add_offer.html', context)


@login_required
@admin_required
@require_POST
def edit_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    data = json.loads(request.body)
    name = data.get('name')
    
    if Offer.objects.filter(name=name).exclude(id=offer_id).exists():
        return JsonResponse({'success': False, 'message': 'An offer with this name already exists.'})
    
    offer.name = name
    offer.description = data.get('description')
    offer.start_date = data.get('start_date')
    offer.end_date = data.get('end_date')
    offer.save()
    
    return JsonResponse({'success': True, 'message': 'Offer updated successfully.'})


@login_required
@admin_required
@require_POST
def delete_offer(request, offer_id):
    try:
        offer = get_object_or_404(Offer, id=offer_id)
        offer.is_active = False
        offer.save()
        messages.success(request, 'Offer deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting offer: {str(e)}')
    return redirect('offers_view')


@login_required
@admin_required
def search_items(request):
    query = request.GET.get('q', '').strip()
    item_type = request.GET.get('type', '')
    
    if not query:
        return JsonResponse({'results': []})
    
    if item_type == 'product':
        items = Product.objects.filter(
            Q(name__istartswith=query) & 
            Q(is_deleted=False)
        ).order_by('name')[:10]  # order by name and limit to 10 results
        results = [{'id': item.id, 'name': item.name} for item in items]
    else:
        items = Category.objects.filter(
            Q(name__istartswith=query) & 
            Q(is_deleted=False)
        ).order_by('name')[:10]  # order by name and limit to 10 results
        results = [{'id': item.id, 'name': item.name} for item in items]
    
    return JsonResponse({'results': results})
