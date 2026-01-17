from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from .models import Address
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from cart.models import Cart,CartItem
from products.models import Size,ProductSize,Wishlist
from offers_coupons.models import Coupon,CouponUsage
from order.models import Order
import os
import uuid
from wallet.models import Wallet

User = get_user_model()
def admin_required(function):
    return user_passes_test(
        lambda user: user.is_superuser,
        login_url='misc_pages:custom_404')(function)
    

@never_cache
@login_required(login_url='authentication:login')
def address(request):
    next_page = request.GET.get('next', None) 
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    wallet_balance = wallet.balance
    address = Address.objects.filter(user=request.user, status='listed').order_by('-id')
    coupon_code=request.POST.get('coupon_code','')
    msg=None
    cart_items = []
    field_errors = {}
    total_price = 0
    cart, _ = Cart.objects.get_or_create(user=request.user) 
 
    if request.method=='POST':
        for item in cart.items.all():
          product_size = get_object_or_404(ProductSize, product=item.product, size=item.size)
          stock=product_size.stock
          item_total = item.product.price * item.quantity
          total_price += item_total
          cart_items.append({
              'product': item.product,
              'quantity': item.quantity,
              'size': item.size,
              'item_total': item_total,
          })
        if coupon_code:
             
                coupon = Coupon.objects.get(code=coupon_code)
                 
             
                discount = coupon.discount
                   
                        
                messages.success(request, f"Coupon applied! You saved ₹{discount}.")
                     
         
        # Use request.user directly
        address_line1=request.POST.get('address_line1').strip()
       
        city=request.POST.get('city','').strip()
        
        state=request.POST.get('state','').strip()
        postal_code=request.POST.get('postal_code','').strip()
        country=request.POST.get('country','').strip()
        phone_number=request.POST.get('phone_number','').strip()
        if not address_line1:
            field_errors['address_line1'] = "Address line is required."
        elif len(address_line1) < 5:
            field_errors['address_line1'] = "Address line must be at least 5 characters long."
        if not city:
            field_errors['city'] = "City is required."
        elif not city.isalpha():
            field_errors['city'] = "City name must contain only letters."
        if not state:
            field_errors['state'] = "State is required."
        elif not state.isalpha():
            field_errors['state'] = "State name must contain only letters."
        if not postal_code:
            field_errors['postal_code'] = "Postal code is required."
        elif not postal_code.isdigit():
            field_errors['postal_code'] = "Postal code must be numeric."
        elif len(postal_code) < 4 or len(postal_code) > 10:
            field_errors['postal_code'] = "Postal code must be between 4 and 10 digits."
        if not country:
            field_errors['country'] = "Country is required."
        if not phone_number:
            field_errors['phone_number'] = "Phone number is required."
        elif not phone_number.isdigit():
            field_errors['phone_number'] = "Phone number must be numeric."
        elif len(phone_number) != 10:
            field_errors['phone_number'] = "Phone number must be exactly 10 digits."
        if not field_errors:
               Address.objects.create(user=request.user,address_line1=address_line1,city=city,state=state,postal_code=postal_code,country=country,phone_number=phone_number)
               messages.success(request, 'Address added successfully!')
               if next_page:
                   return redirect(next_page)
               return redirect('user_profile:address')
        
        if next_page:
            # Re-fetch everything needed for payment.html if we must render it due to errors
            # But redirecting with messages might be better. However, field_errors won't persist.
            # For now, we render it but the modal will reopen via JS.
            context = {
                'cart_items': cart_items,
                'addresses': address,
                'next_page': next_page,
                'address_line1': address_line1,
                'city': city,
                'state': state,
                'postal_code': postal_code,
                'country': country,
                'phone_number': phone_number,
                'field_errors': field_errors,
                'has_errors': True,
                'coupon_code': coupon_code,
                'total_price': total_price - (discount if 'discount' in locals() else 0),
                'discount': discount if 'discount' in locals() else 0,
                'wallet_balance': wallet_balance,
            }
            return render(request, 'cart/payment.html', context)
        return redirect('user_profile:address')
     
    context={
        'address':address,
        'cart_items':cart_items,
        'msg':msg,
        'next_page': next_page,
        'field_errors':field_errors,
        'wallet_balance':wallet_balance,

    }
    return render(request,'user_profile/address.html',context)  

@never_cache
@login_required(login_url='authentication:login')          
def editaddress(request,id):
    address = get_object_or_404(Address, id=id) 
    msg1=None
    if request.method=='POST':
       address.address_line1=request.POST.get('address_line1').strip()
       address.city=request.POST.get('city').strip()
       address.state=request.POST.get('state').strip()
       address.postal_code=request.POST.get('postal_code').strip()
       address.country=request.POST.get('country').strip()
       address.phone_number=request.POST.get('phone_number').strip()
       address.save()
       msg1='updated sucessfully'
       return redirect('user_profile:address')
    context={
        'address':address,
        'msg1':msg1
    }
    return render(request,'user_profile/address.html',context)

@never_cache
@login_required(login_url='authentication:login')                
def listaddress(request,id):
    if request.method=='POST':
        address=get_object_or_404(Address,id=id)
        if address.status=='listed':
            address.status='dislisted'
        address.save()
        return redirect('user_profile:address')  
    return render(request,'user/address.html') 
 
@never_cache
@admin_required
def blockuser(request,id):
    user=User.objects.get(id=id)
    user.is_active=not user.is_active
    user.save()
    return redirect('user_profile:users')

@never_cache
@admin_required
def users(request):
    User = get_user_model()
    users = User.objects.filter(is_superuser=False).order_by('-id')
    context={
        'users':users
    }
    return render(request,'user_profile/users.html',context)

@never_cache
@login_required(login_url='authentication:login')
def profile(request):
    user = request.user
    
    # Statistics
    total_orders_count = Order.objects.filter(user=user).count()
    wishlist_items_count = Wishlist.objects.filter(user=user).count()
    
    wallet, _ = Wallet.objects.get_or_create(user=user)
    wallet_balance = wallet.balance
    
    # Recent Acquisitions (Orders)
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:2]
    
    # Wishlist Preview
    wishlist_preview = Wishlist.objects.filter(user=user).select_related('product').order_by('-added_at')[:2]

    if request.method == 'POST' and request.FILES.get('profile_picture'):
        profile_picture = request.FILES.get('profile_picture')
        ext = os.path.splitext(profile_picture.name)[1]  
        new_filename = f"profile_{uuid.uuid4().hex[:10]}{ext}"
        profile_picture.name = new_filename
        user.profile_image = profile_picture
        user.save()
        messages.success(request, "Avatar updated in the vault.")
        return redirect('user_profile:profile')
        
    context = {
        'user': user,
        'total_orders_count': total_orders_count,
        'wishlist_items_count': wishlist_items_count,
        'wallet_balance': wallet_balance,
        'recent_orders': recent_orders,
        'wishlist_preview': wishlist_preview,
    }
    return render(request, 'user_profile/profile.html', context)
@never_cache
@login_required(login_url='authentication:login')
def editprofile(request):
    user=request.user
    if request.method=='POST':
        user.phone=request.POST.get('phone')
        user.dob=request.POST.get('dob')
        user.gender=request.POST.get('gender')
        user.city=request.POST.get('city')
        user.country=request.POST.get('country')
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('user_profile:profile')
    return render(request,'user/profile.html')

@never_cache
@login_required(login_url='authentication:login')
def change_password(request):
    error_messageprofile=None
    modal_open = False
 
    if request.method=="POST":
    
        currentpassword=request.POST.get('current_password')
        newpasssword=request.POST.get('new_password')
        comfirmpassword=request.POST.get('confirm_password')
        if not request.user.check_password(currentpassword):
            error_messageprofile= "The current password is incorrect."
            modal_open = True
 
            return render(request, 'user_profile/profile.html', {
                'error_messageprofile': error_messageprofile,
                'modal_open': modal_open
            })
        if newpasssword!=comfirmpassword:
            error_messageprofile= "The new passwords do not match."
            modal_open = True
            return render(request, 'user_profile/profile.html', {
                'error_messageprofile': error_messageprofile,
                'modal_open': modal_open
            })
        if newpasssword:
            request.user.set_password('newpasssword')
            request.user.save()
            
            update_session_auth_hash(request, request.user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('user_profile:profile')
        else:
            messages.error(request, "Please enter a valid new password.")
            return redirect('change_password')
    context={
        'error_messageprofile':error_messageprofile,
        'modal_open':modal_open
    }
    return render(request,'user_profile/profile.html',context)