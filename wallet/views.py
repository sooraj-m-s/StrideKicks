from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from .models import Wallet, WalletTransaction


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
