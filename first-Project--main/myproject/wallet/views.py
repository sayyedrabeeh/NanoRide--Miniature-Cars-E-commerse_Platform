from django.shortcuts import render
from .models import Wallet,Transaction
from django.contrib.auth.decorators import login_required

# Create your views here.
# @login_required
@login_required(login_url='authentication:login')    

def wallet(request): 
    wallet, created = Wallet.objects.get_or_create(user=request.user)

    
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'wallet': wallet,
        'transactions': transactions,
    }

    return render(request, 'wallet/wallet.html', context)