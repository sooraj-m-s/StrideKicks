from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.db.models import Q
from utils.decorators import admin_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.exceptions import ValidationError
import json
from .models import Wallet, WalletTransaction, Offer


# Create your views here.


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def wallet_view(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')[:10]
    
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
        Q(offer_name__icontains=search_query) |
        Q(offer_type__icontains=search_query)
    ).order_by('-created_at')

    context = {
        'offers': offers,
        'search_query': search_query,
        'offer_types': Offer.OFFER_TYPES,
        'first_name': request.user.first_name,
    }
    return render(request, 'add_offer.html', context)


@login_required
@admin_required
@require_POST
def create_offer(request):
    try:
        data = json.loads(request.body)
        start_date = timezone.make_aware(timezone.datetime.fromisoformat(data['start_date']))
        end_date = timezone.make_aware(timezone.datetime.fromisoformat(data['end_date']))

        offer_name = data['offer_name']
        if len(offer_name.strip()) < 4:
            raise ValueError('Enter a valid offer name.')
        if Offer.objects.filter(offer_name__iexact=offer_name).exists():
            raise ValidationError('An offer with this name already exists.')

        new_offer = Offer.objects.create(
            offer_name=data['offer_name'],
            offer_type=data['offer_type'],
            discount_value=data['discount_value'],
            min_purchase_amount=data['min_purchase_amount'],
            max_discount_amount=data['max_discount_amount'],
            start_date=start_date,
            end_date=end_date,
            usage_limit=data['usage_limit'],
            is_exclusive=data['is_exclusive']
        )
        return JsonResponse({'success': True, 'message': 'Offer created successfully'})
    except ValidationError as e:
        return JsonResponse({'success': False, 'message': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})


@login_required
@admin_required
@require_POST
def edit_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    data = json.loads(request.body)
    offer_name = data.get('offer_name')
    
    if Offer.objects.filter(offer_name=offer_name).exclude(id=offer_id).exists():
        return JsonResponse({'success': False, 'message': 'An offer with this name already exists.'})
    
    offer.offer_name = offer_name
    offer.offer_type = data.get('offer_type')
    offer.product_id = data.get('product')
    offer.brand_id = data.get('brand')
    offer.category_id = data.get('category')
    offer.discount_value = data.get('discount_value')
    offer.min_purchase_amount = data.get('min_purchase_amount')
    offer.max_discount_amount = data.get('max_discount_amount')
    offer.start_date = data.get('start_date')
    offer.end_date = data.get('end_date')
    offer.usage_limit = data.get('usage_limit')
    offer.is_exclusive = data.get('is_exclusive', False)
    offer.save()
    
    return JsonResponse({'success': True, 'message': 'Offer updated successfully.'})


@login_required
@admin_required
@require_POST
def delete_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    offer.delete()
    return JsonResponse({'success': True, 'message': 'Offer deleted successfully.'})
