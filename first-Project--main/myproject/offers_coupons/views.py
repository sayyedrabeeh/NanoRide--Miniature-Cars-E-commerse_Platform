from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from .models import Coupon
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required


def admin_required(function):
    return user_passes_test(
        lambda user: user.is_superuser,
        login_url='misc_pages:custom_404')(function)

@never_cache
@login_required(login_url='authentication:login')
def coupon(request, coupon_id=None):
    coupons = Coupon.objects.all()
    if coupon_id:
        coupon = get_object_or_404(Coupon, id=coupon_id)
    else:
        coupon = None
    if request.method == 'POST':
        code = request.POST.get('code')   
        discount = int(request.POST.get('discount'))   
   
        if coupon:
      
         coupon.code = code
         coupon.discount = discount
 
         if discount > 200:
             messages.error(request, "Coupon discount must be under ₹200.")
             return redirect('offers_coupons:coupon')
         else:
             coupon.save()  
             messages.success(request, "Coupon updated successfully.")
             return redirect('offers_coupons:coupon')
        else:
            if Coupon.objects.filter(code=code).exists():
                messages.error(request, "Coupon code already exists.")
                return redirect('offers_coupons:coupon')
            elif discount > 200 or discount <=0 :
                messages.error(request, "Coupon discount must be b/w 0 to ₹200.")
                return redirect('offers_coupons:coupon')
            Coupon.objects.create(
                code=code,
                discount=discount,
            )
            messages.success(request, "New coupon created successfully.")
        return redirect('offers_coupons:coupon')  
    context = {
        'coupons': coupons,
        'coupon': coupon
    }
    return render(request, 'offers_coupons/coupon.html', context)
 
@never_cache
@login_required(login_url='authentication:login')
def listcoupon(request,id):
    coupon=Coupon.objects.get(id=id)
    coupons=Coupon.objects.all()
    if coupon.status=='listed':
            coupon.status='dislisted'
    else:
            coupon.status='listed'
    coupon.save()
    context={
        'coupons':coupons
    }
    return render(request,'offers_coupons/coupon.html',context)
