from django.shortcuts import render,redirect
from .models import Cart,CartItem
from django.shortcuts import get_object_or_404
from products.models import Product
from order.models import OrderItem,Order
from user_profile.models import Address
from django.contrib.auth.decorators import login_required
from products.models import Size,ProductSize
from django.contrib import messages 
from django.views.decorators.cache import never_cache
from offers_coupons.models import Coupon,CouponUsage
from django.http import JsonResponse
import json
import razorpay
from django.db.models import Sum
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from django.utils.crypto import get_random_string
from wallet.models import Transaction, Wallet

@never_cache
@login_required(login_url='authentication:login')
def cart_view(request, action=None):
    try:
         cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = None
    if request.method=='POST' and  action=='add':
        product_id=request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        product_size_id = request.POST.get('product_size')
        if product_size_id:
            product_size = get_object_or_404(ProductSize, id=product_size_id)
            size = product_size.size
        else:
            # Fallback for pages without size selectors (like brand list) or data issues
            ps = ProductSize.objects.filter(product=product).first()
            if not ps:
                # Auto-initialize a Standard size if the admin hasn't set any
                standard_size, _ = Size.objects.get_or_create(name="Standard")
                ps = ProductSize.objects.create(product=product, size=standard_size, stock=10)
            size = ps.size
        quantity = int(request.POST.get('quantity', 1))    
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product, size=size)
        if item_created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity
        cart_item.save() 
        messages.success(request, f"{product.name} added to your collection.")
        return redirect('cart:cart_view')
    elif request.method=='POST' and action=='remove':
        product_id=request.POST.get('product_id')
        size_id=request.POST.get('size_id')
        cart = Cart.objects.get(user=request.user)
        CartItem.objects.filter(cart=cart, product__id=product_id, size__id=size_id).delete()
        return redirect('cart:cart_view')
    if request.method == 'POST' and action == 'update_quantity':
        product_id = request.POST.get('product_id')
        size_id = request.POST.get('size_id')
        new_quantity = int(request.POST.get('quantity', 1))
        
        try:
            cart_item = CartItem.objects.get(cart=cart, product__id=product_id, size__id=size_id)
            product_size = ProductSize.objects.get(product=cart_item.product, size=cart_item.size)

            if new_quantity > product_size.stock:
                messages.error(request, f"Only {product_size.stock} items available for {cart_item.product.name}.")
            else:
                cart_item.quantity = new_quantity
                cart_item.save()
        except CartItem.DoesNotExist:
            messages.error(request, "Cart item not found.")
        except ProductSize.DoesNotExist:
            messages.error(request, "Invalid product size.")

        return redirect('cart:cart_view')
    cart_items = []
    total_price = 0
    out_of_stock_items = []  
    error_messages = []  
    total_discount = 0
    applied_coupon = None   
    coupon_message = ""
    discount = 0
    total_price1 = 0
    coupons = Coupon.objects.filter(status='listed').exclude(
        id__in=CouponUsage.objects.filter(user=request.user).values('coupon')
    )
    if cart:
        discount = cart.discount
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
                'stock': product_size.stock,  
            })
            if stock < item.quantity:
                out_of_stock_items.append(item)
                messages1='seleted product is out of stock'
                 
    total_price1=total_price-discount
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'out_of_stock_items': out_of_stock_items,
        'addresses' : Address.objects.filter(user=request.user, status='listed'),
        'coupons' : coupons,
        'discount':discount,
        'total_price1':total_price1,
        
    }
    return render(request, 'cart/cart.html', context)

@never_cache
@login_required(login_url='authentication:login')
def payment(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    wallet_balance = wallet.balance
    coupon_code=request.POST.get('coupon_code','')
    cart = Cart.objects.get(user=request.user)
    total_price = 0
    discount =  0
    cart_items = []
    out_of_stock_items = [] 
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
        if stock < item.quantity:
            out_of_stock_items.append(item)
            return redirect('cart:cart_view')
    
    # Initialize discount if not already set via POST
    if 'discount' not in locals():
        discount = 0
        
    total_price_in_paise = int((total_price - discount) * 100)  

    min_order_amount = 1  
    if total_price_in_paise < min_order_amount:
        context = {
            'error': "Order amount is less than the minimum allowed amount.",
            'cart_items': cart_items,
            'total_price': total_price,
            # 'discount': discount,
        }
        return render(request, 'cart/cart.html', context)

    if request.method == "POST":
        shipping_address_id = request.POST.get('selected_address')
        payment_method = request.POST.get('payment_method')
        coupon_code = request.POST.get('coupon_code', '').strip()
        discount = request.POST.get('discount')
    
        message = ""
        
        discount =Decimal(discount)
     
        total_price_in_paise = int((total_price - discount) * 100)  
      

        if not shipping_address_id or not payment_method:
   
            context = {
                'error': "Please Add a shipping address and payment method.",
                'cart_items': cart_items,
                'total_price': total_price - discount,
                'addresses': Address.objects.filter(user=request.user, status='listed'),
                'wallet_balance': wallet_balance,
                'discount': discount,
                'coupon_code': coupon_code
            }
            return render(request, 'cart/payment.html', context)
      
        shipping_address = get_object_or_404(Address, id=shipping_address_id, user=request.user)
     
        order = Order.objects.create(
            user=request.user,
            shipping_address=shipping_address,
            total_price=total_price - discount,
            payment_type=payment_method,
            coupon_used=True if discount > 0 else False,
            coupon_code=coupon_code if discount > 0 else None,
            created_at=timezone.now(),
        )
        for item in cart.items.all():
            product_size = get_object_or_404(ProductSize, product=item.product, size=item.size)
            if product_size.stock == 0:
                continue
            if item.quantity <= product_size.stock:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    size=item.size,
                    quantity=item.quantity,
                    price=item.product.price,
                    subtotal_price=item.product.price * item.quantity,
                )
                product_size.stock -= item.quantity
                product_size.save()
                item.delete()
            else:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    size=item.size,
                    quantity=product_size.stock,
                    price=item.product.price,
                    subtotal_price=item.product.price * product_size.stock,
                )
                remaining_quantity = item.quantity - product_size.stock
                item.quantity = remaining_quantity
                item.save()
                product_size.stock = 0
                product_size.save()
            if coupon_code:
               try:
                   coupon = Coupon.objects.get(code=coupon_code)
                   if not CouponUsage.objects.filter(user=request.user, coupon=coupon).exists():
                       CouponUsage.objects.create(user=request.user, coupon=coupon)
                   else:
                      messages.error(request, "Coupon already used by this user.")
               except Coupon.DoesNotExist:
                          messages.error(request, "Invalid coupon code.")
        if payment_method == 'razorpay':
            discounted_price = total_price - discount
            total_price_in_paise = int(discounted_price * 100)
            
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            data = {
                "amount": total_price_in_paise,
                "currency": "INR",
                "receipt": f"order_{order.order_id}",
            }
            razorpay_order = client.order.create(data=data)
            razorpay_order_id = razorpay_order['id']
            order.razorpay_order_id = razorpay_order_id
            order.save()
            context = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'total_price': float(total_price - discount),   
                'total_price_in_paise': total_price_in_paise,
                'cart_items': cart_items,
                'order_id': order.order_id,
                'addresses': Address.objects.filter(user=request.user, status='listed'),
                'discount': float(discount),
                'coupon_code': coupon_code,
                'wallet_balance': float(wallet_balance),
                'payment_method': payment_method,
            }
            
            return render(request, 'cart/payment.html', context)
        elif payment_method=='wallet':
            # order = get_object_or_404(Order, order_id=order_id)
            transaction_id = get_random_string(length=20)  
            transaction = Transaction.objects.create(
                    user=request.user,
                    transaction_id=transaction_id,
                    amount=total_price,
                    status='Completed',   
                    transaction_type='Debit'  
                )
            order.payment = 'Success'
            order.payment_status = 'Success'
            order.save()
            wallet.balance-=total_price
            wallet.save()
            return redirect('cart:success_page')
        elif payment_method =='cod': 
            order.payment= 'pending'

            order.save()
            return redirect('cart:success_page')
        return redirect('cart:success_page')

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'discount': discount,
        'addresses' : Address.objects.filter(user=request.user, status='listed'),
        'wallet_balance': wallet_balance  
    }
    return render(request, 'cart/payment.html', context)
def success_page(request):
    cancel = request.GET.get('cancel', False)
    order_id = request.GET.get("order_id")
    order = None
    subtotal = 0
    discount = 0
    
    if order_id:
        order = get_object_or_404(Order, order_id=order_id)
        if not cancel:
            order.payment = 'Success'
            order.payment_status = 'Success'
            order.save()
        
        # Calculate subtotal and discount
        subtotal = sum(item.subtotal_price for item in order.items.all())
        discount = subtotal - order.total_price
    
    # Recommendations
    recommended_products = Product.objects.filter(status='listed').order_by('?')[:4]
    
    context = {
        'order': order,
        'order_id': order_id,
        'cancel': cancel,
        'recommended_products': recommended_products,
        'subtotal': subtotal,
        'discount': discount
    }
    return render(request, 'cart/success.html', context)

def apply_coupon(request):
     try:
         cart = Cart.objects.get(user=request.user)
     except Cart.DoesNotExist:
         messages.error(request, "Your cart is empty.")
         return redirect('cart:cart_view')
     cart_items = []
     total_price = 0
     wallet, created = Wallet.objects.get_or_create(user=request.user)
     wallet_balance = wallet.balance
     for item in cart.items.all():
         product_size = get_object_or_404(ProductSize, product=item.product, size=item.size)
         item_total = item.product.price * item.quantity
         total_price += item_total
         cart_items.append({
             'product': item.product,
             'quantity': item.quantity,
             'size': item.size,
             'item_total': item_total,
         })
     
     discount = 0
     coupon_code = None
     
     if request.method == 'POST':
         coupon_code = request.POST.get('coupon_code', '').strip()
         if 'remove_coupon' in request.POST:   
           CouponUsage.objects.filter(user=request.user, coupon__code=coupon_code).delete()
           coupon_code = None
           messages.success(request,"removed")
         elif coupon_code:
             try:
                 coupon = Coupon.objects.get(code=coupon_code)
                 if not coupon.is_active():
                     messages.error(request, "This coupon is either inactive or has reached its usage limit.")
                     context={
                         'cart_items': cart_items,
                         'addresses': Address.objects.filter(user=request.user, status='listed'),
                         'total_price':total_price,
                         'wallet_balance':wallet_balance
                     }
                     return render(request, 'cart/payment.html',context)
                 elif CouponUsage.objects.filter(user=request.user, coupon=coupon).exists():
                     messages.error(request, "You have already applied this coupon.")
                     context={
                         'cart_items': cart_items,
                         'addresses': Address.objects.filter(user=request.user, status='listed'),
                         'total_price':total_price,
                         'wallet_balance':wallet_balance
                     }
                     return render(request, 'cart/payment.html',context)
                 else:
                     order = Order.objects.filter(user=request.user)
                     discount = coupon.discount
                     if total_price >= 1000:
                         # order.coupon_code = coupon.code
                         # order.save()
                        #  CouponUsage.objects.create(user=request.user, coupon=coupon)
              
                         messages.success(request, f"Coupon applied! You saved ₹{discount}.")
                     else:
                        messages.error(
                             request,
                             f"This coupon is valid only for orders above ₹1000."
                         )
                        context={
                         'cart_items': cart_items,
                         'addresses': Address.objects.filter(user=request.user, status='listed'),
                         'total_price':total_price,
                         'wallet_balance':wallet_balance,
                         'discount':discount
                         }
                        return render(request, 'cart/payment.html',context)
             except Coupon.DoesNotExist:
                 messages.error(request, "Invalid coupon code.")
                 context={
                         'cart_items': cart_items,
                         'addresses': Address.objects.filter(user=request.user, status='listed'),
                         'total_price':total_price,
                         'wallet_balance':wallet_balance
                     }
                 return render(request, 'cart/payment.html',context)
         else:
             messages.error(request, "Please enter a coupon code.")
     return render(request, 'cart/payment.html', {
         'cart_items': cart_items,
         'total_price': total_price - discount,
         'discount': discount,
         'addresses': Address.objects.filter(user=request.user, status='listed'),
         'coupon_code':coupon_code,
         'wallet_balance':wallet_balance
     })
