from django.shortcuts import render
from .models import Categories,Product,ProductImage, Size,ProductSize,Types
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.db.models import Count, Avg, Sum
from django.urls import reverse
from django.core.files.base import ContentFile
import base64
import json
from django.db.models import F
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from cart.models import CartItem
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from decimal import Decimal, InvalidOperation
from .models import Wishlist
from django.db.models import Q
 

def admin_required(function):
    return user_passes_test(
        lambda user: user.is_superuser,
        login_url='misc_pages:custom_404')(function)
def home(request):
    products = Product.objects.filter(status='listed')
    catogery = Categories.objects.filter(status='listed')
    page_number = request.GET.get('page', 1)
    if request.user.is_authenticated:
        cart_items_count = CartItem.objects.filter(cart__user=request.user).count()
        user_wishlist = Wishlist.objects.filter(user=request.user).values_list('product', flat=True)
    else:
        cart_items_count = 0
        user_wishlist = []
    
    product = None
    if 'product_id' in request.GET:
        product_id = request.GET['product_id']
        product = get_object_or_404(Product, id=product_id)
    paginator = Paginator(products, 12)
    try:
        paginated_products = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_products = paginator.page(1)  
    except EmptyPage:
        paginated_products = paginated_products = paginator.page(paginator.num_pages) 
    context = {
        'catogery': catogery,
        'products': paginated_products,
        'product': product,
        'cart_items_count': cart_items_count,
        'user_wishlist': user_wishlist,
    }
    return render(request, 'products/home.html', context)
@never_cache
def products(request):
    query = request.GET.get('q', '')  
    sort_by = request.GET.get('sort', 'default')   
    page_number = request.GET.get('page', 1)  
 
    category_ids = request.GET.getlist('category')
    if category_ids:
        products = Product.objects.filter(category__id__in=category_ids, status='listed')
    else:
        products = Product.objects.filter(status='listed')
    type_ids = request.GET.getlist('type')   
    if type_ids:
        products = products.filter(Types__id__in=type_ids)

    
    brand_names = request.GET.getlist('brand')
    if brand_names:
        products = products.filter(category__brand_name__in=brand_names)

  
    min_price = request.GET.get('min_price', None)
    max_price = request.GET.get('max_price', None)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Filter by query search
    if query:
        products = products.filter(name__icontains=query)

    # Sorting logic
    if sort_by == 'popularity':
        products = products.annotate(popularity=Count('comments')).order_by('-popularity')
    elif sort_by == 'rating':
        products = products.annotate(avg_rating=Avg('ratings')).order_by('-avg_rating')
    elif sort_by == 'newness':
        products = products.order_by('-created_at')
    elif sort_by == 'price_low_to_high':
        products = products.order_by('price')
    elif sort_by == 'price_high_to_low':
        products = products.order_by('-price')
    elif sort_by == 'a_z':
        products = products.order_by('name')
    elif sort_by == 'z_a':
        products = products.order_by('-name')

    # Pagination
    paginator = Paginator(products, 12)
    try:
        paginated_products = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_products = paginator.page(1)
    except EmptyPage:
        paginated_products = paginator.page(paginator.num_pages)

  
    categories = Categories.objects.filter(status='listed').order_by('-id')
    Type=Types.objects.filter(status='listed').order_by('-id')

  
    if request.user.is_authenticated:
        cart_items_count = CartItem.objects.filter(cart__user=request.user).count()
        user_wishlist = Wishlist.objects.filter(user=request.user).values_list('product', flat=True)
    else:
        cart_items_count = 0
        user_wishlist = []

    context = {
        'products': paginated_products,
        'categories': categories,
        'query': query,
        'Type':Type,
        'sort_by': sort_by,
        'cart_items_count': cart_items_count,
        'min_price': min_price,
        'max_price': max_price,
        'category_ids': category_ids,
        'brand_names': brand_names,
        'user_wishlist':user_wishlist
    }

    return render(request, 'products/products.html', context)
@never_cache
def products_detail(request, id):
    product = get_object_or_404(Product, id=id)
    sizes_with_stock = ProductSize.objects.filter(product=product).select_related('size').order_by('size__id') 
   
    if request.user.is_authenticated:
        cart_items_count = CartItem.objects.filter(cart__user=request.user).count()
    else:
        cart_items_count = 0

    categories = Categories.objects.filter(status='listed').order_by('-id')
    sizes_stock = [
        {
            'id': ps.id,
            'name': ps.size.name,
            'stock': ps.stock
        }
        for ps in sizes_with_stock
    ]
    related_products = Product.objects.filter(category=product.category, status='listed').exclude(id=id)[:4]

    context = {
        'product': product,
        'sizes_stock': sizes_stock,
        'cart_items_count': cart_items_count,
        'categories':categories,
        'related_products': related_products
    }
    return render(request, 'products/product_detail.html', context)
@login_required(login_url='authentication:login')    
def brand_products(request, brand_name):
    sort_by = request.GET.get('sort', 'default')   
    page_number = request.GET.get('page', 1)  
    
    # Base products filtered by brand
    products = Product.objects.filter(category__brand_name=brand_name, status='listed')

    # Filtering by type
    type_ids = request.GET.getlist('type')   
    if type_ids:
        products = products.filter(Types__id__in=type_ids)
    
    # Filter by price range
    min_price = request.GET.get('min_price', None)
    max_price = request.GET.get('max_price', None)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Sorting logic
    if sort_by == 'popularity':
        products = products.annotate(popularity=Count('comments')).order_by('-popularity')
    elif sort_by == 'rating':
        products = products.annotate(avg_rating=Avg('ratings')).order_by('-avg_rating')
    elif sort_by == 'newness':
        products = products.order_by('-created_at')
    elif sort_by == 'price_low_to_high':
        products = products.order_by('price')
    elif sort_by == 'price_high_to_low':
        products = products.order_by('-price')
    elif sort_by == 'a_z':
        products = products.order_by('name')
    elif sort_by == 'z_a':
        products = products.order_by('-name')

    # Pagination
    paginator = Paginator(products, 12)
    try:
        paginated_products = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_products = paginator.page(1)
    except EmptyPage:
        paginated_products = paginator.page(paginator.num_pages)

    # Metadata for filter sidebar
    available_types = Types.objects.filter(status='listed').order_by('-id')

    # Wishlist status
    if request.user.is_authenticated:
        user_wishlist = Wishlist.objects.filter(user=request.user).values_list('product', flat=True)
    else:
        user_wishlist = []

    context = {
        'products': paginated_products,
        'brand_name': brand_name,
        'available_types': available_types,
        'selected_types': [int(i) for i in type_ids if i.isdigit()],
        'sort_by': sort_by,
        'min_price': min_price,
        'max_price': max_price,
        'user_wishlist': user_wishlist,
    }
    return render(request, 'products/brand_products.html', context)
@never_cache
@admin_required
def catogery(request):
    action=request.POST.get('action')
    if request.method=='POST':
        if action =='add':
            brand_name=request.POST.get('brand_name').strip()
            offer=request.POST.get('offer',0).strip()
            status=request.POST.get('status','True').strip()
            if not brand_name:
                messages.error(request, "Brand name is required.")
                return redirect('products:catogery')

            if Categories.objects.filter(brand_name__iexact=brand_name).exists():
                messages.error(request, "A category with this brand name already exists.")
                return redirect('products:catogery')
            try:
                if offer == '':
                    offer = 0   
                else:
                    offer = Decimal(offer)
                if offer < 0 or offer > 80:
                    raise ValueError("Offer must be between 0 and 80.")
            except (InvalidOperation, ValueError) as e:
                messages.error(request, f"Invalid offer: {e}")
                return redirect('products:catogery')

            featured = request.POST.get('featured') == 'on'

            catogery=Categories.objects.create(
                brand_name=brand_name,
                active=status == 'True',
                offer=offer,
                featured=featured
            )
            catogeryimage = request.FILES.get('catogeryimage')
            if catogeryimage:
               catogery.image = catogeryimage
               catogery.save()
           
            messages.success(request, "Category added successfully!")
            return redirect('products:catogery')
        elif action=='edit'  :
        
            category_id = request.POST.get('catogery_id')
            category_obj = get_object_or_404(Categories, id=category_id)
            brand_name = request.POST.get('brand_name', '').strip()
            offer = request.POST.get('offer', '').strip()
            active = request.POST.get('active', 'True').strip()
            image = request.FILES.get('image')
    
            # Validation
            if not brand_name:
                messages.error(request, "Category name is required.")
                return redirect('products:catogery')
    
            if Categories.objects.filter(brand_name__iexact=brand_name).exclude(id=category_id).exists():

                messages.error(request, "A type with this category name already exists.")
                return redirect('products:catogery')
    
            try:
                offer = Decimal(offer) if offer else 0
                if offer < 0 or offer > 80:
                    raise ValueError("Offer must be between 0 and 80.")
            except (InvalidOperation, ValueError) as e:
                messages.error(request, f"Invalid offer: {e}")
                return redirect('products:catogery')
    
        
            featured = request.POST.get('featured') == 'on'
    
            category_obj.brand_name = brand_name
            category_obj.offer = offer
            category_obj.active = active == 'True'
            category_obj.featured = featured
    
            if image:
                category_obj.image.save(image.name, image)
    
            category_obj.save()
            messages.success(request, "Category updated successfully!")
            return redirect('products:catogery')
        elif action =='toggle':
            catogery_id=request.POST.get('catogery_id')
            catogery=get_object_or_404(Categories,id=catogery_id)
            if catogery.status=='listed':
                catogery.status='dislisted'
            else:
                catogery.status='listed'
            catogery.save()
        elif action == 'delete':
            category_id = request.POST.get('catogery_id')
            category_obj = get_object_or_404(Categories, id=category_id)
            category_obj.delete()
            messages.success(request, "Category deleted successfully!")
        return redirect('products:catogery')
    error_message = None
    modal_open = False
    search_query = request.GET.get('search', '')
    categories = Categories.objects.all()
    if search_query:
        categories = categories.filter(brand_name__icontains=search_query)
    sort_field = request.GET.get('sort', '-id')   
    categories = categories.order_by(sort_field)
    
    # Calculate Statistics
    total_categories = Categories.objects.count()
    active_categories = Categories.objects.filter(active=True).count()
    hidden_categories = Categories.objects.filter(status='dislisted').count()
    featured_categories = Categories.objects.filter(featured=True).count()
    
    paginator = Paginator(categories, 5)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'categories': page_obj,
        'error_message': error_message,
        'modal_open': modal_open,
        'search_query': search_query,
        'sort_field': sort_field,
        'total_categories': total_categories,
        'active_categories': active_categories,
        'hidden_categories': hidden_categories,
        'featured_categories': featured_categories,
    }
    return render(request, 'products/catogery.html', context)

def Type(request):
    
    action=request.POST.get('action')
    if request.method=='POST':
        if action =='add':
            category = request.POST.get('category', '').strip()
            offer = request.POST.get('offer', '').strip()
            status = request.POST.get('status', 'True').strip()
               
            if not category:
                messages.error(request, "Category name is required.")
                return redirect('products:Type')

            if Types.objects.filter(category__iexact=category).exists():
                messages.error(request, "A type with this category name already exists.")
                return redirect('products:Type')

            try:
                if offer == '':
                    offer = 0   
                else:
                    offer = Decimal(offer)
                if offer < 0 or offer > 80:
                    raise ValueError("Offer must be between 0 and 80.")
            except (InvalidOperation, ValueError) as e:
                messages.error(request, f"Invalid offer: {e}")
                return redirect('products:catogery')

             
            catogery=Types.objects.create(
                category=category,
                active=status,
                offer=offer
            )
            catogeryimage = request.FILES.get('catogeryimage')
            if catogeryimage:
                catogery.image.save(catogeryimage.name, catogeryimage)
                catogery.save()        
           
            messages.success(request, "Category added successfully!")
            return redirect('products:Type')
            catogery.save()
        elif action == 'edit':
            category_id = request.POST.get('catogery_id')
            category_obj = get_object_or_404(Types, id=category_id)
            category = request.POST.get('category', '').strip()
            offer = request.POST.get('offer', '').strip()
            active = request.POST.get('active') == 'True'
            image = request.FILES.get('image')
    
            # Validation
            if not category:
                messages.error(request, "Category name is required.")
                return redirect('products:Type')
    
            if Types.objects.filter(category__iexact=category).exclude(id=category_id).exists():
                messages.error(request, "A type with this category name already exists.")
                return redirect('products:Type')
    
            try:
                offer = Decimal(offer) if offer else 0
                if offer < 0 or offer > 80:
                    raise ValueError("Offer must be between 0 and 80.")
            except (InvalidOperation, ValueError) as e:
                messages.error(request, f"Invalid offer: {e}")
                return redirect('products:Type')
    
            # Update Category
            category_obj.category = category
            category_obj.offer = offer
            category_obj.active = active
    
            if image:
                category_obj.image.save(image.name, image)
    
            category_obj.save()
            messages.success(request, "Category updated successfully!")
            return redirect('products:Type')
        elif action =='toggle':
            catogery_id=request.POST.get('catogery_id')
          
            catogery=get_object_or_404(Types,id=catogery_id)
            if catogery.status=='listed':
                catogery.status='dislisted'
            else:
                catogery.status='listed'
            catogery.save()
        elif action == 'delete':
            category_id = request.POST.get('catogery_id')
            category_obj = get_object_or_404(Types, id=category_id)
            category_obj.delete()
            messages.success(request, "Type deleted successfully!")
        return redirect('products:Type')
    
    error_message = None
    modal_open = False
    search_query = request.GET.get('search', '')
    categories = Types.objects.all()
    if search_query:
        categories = categories.filter(category__icontains=search_query)
    sort_field = request.GET.get('sort', '-id')
    valid_sort_fields = ['id', '-id', 'category', '-category', 'offer', '-offer', 'status', '-status']
    if sort_field not in valid_sort_fields:
        sort_field = '-id'   
    categories = categories.order_by(sort_field)

    # Calculate Statistics
    total_types = Types.objects.count()
    active_types = Types.objects.filter(active=True).count()
    inactive_types = Types.objects.filter(active=False).count()
    types_in_use = Types.objects.annotate(product_count=Count('product')).filter(product_count__gt=0).count()

    paginator = Paginator(categories, 5)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'categories': page_obj,
        'error_message': error_message,
        'modal_open': modal_open,
        'search_query': search_query,
        'sort_field': sort_field,
        'total_types': total_types,
        'active_types': active_types,
        'inactive_types': inactive_types,
        'types_in_use': types_in_use,
    }
    return render(request, 'products/Type.html', context)





@login_required(login_url='authentication:login')    
def wishlist(request, action, product_id=None):
    
    if action == 'view':
        wishlist_items = Wishlist.objects.filter(user=request.user)
        return render(request, 'products/wishlist.html', {'wishlist_items': wishlist_items})
    elif action == 'add' and product_id:
        product = get_object_or_404(Product, id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if created:
            messages.success(request, f"{product.name} has been added to your wishlist!")
        else:
            messages.info(request, f"{product.name} is already in your wishlist.")
       
        return redirect(f"{request.META.get('HTTP_REFERER')}#wishlist-section")
    elif action == 'remove' and product_id:
        product = get_object_or_404(Product, id=product_id)
        wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()
        if wishlist_item:
            wishlist_item.delete()
            messages.success(request, f"{product.name} has been removed from your wishlist.")
        else:
            messages.info(request, f"{product.name} was not in your wishlist.")
        # Redirect back to the same page and focus on the wishlist section
        return redirect(f"{request.META.get('HTTP_REFERER')}#wishlist-section")
    messages.error(request, "Invalid action.")
    return redirect(request.META.get('HTTP_REFERER'))
  
@never_cache
@admin_required 

def products_admin(request):
    # Ensure standard car scales exist
    standard_scales = ["1:18", "1:24", "1:43", "1:64"]
    for scale in standard_scales:
        Size.objects.get_or_create(name=scale)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Add a new product
        if action == 'add':
            product_name = request.POST.get('product_name')
            size_data = request.POST.getlist('size')
           
            if not size_data:
                messages.error(request, "Please select at least one size.")
                return redirect('products:products_admin')

            try:
                price = Decimal(request.POST.get('price', '0'))  
            except InvalidOperation:
                price = Decimal('0')   
    
            try:
                offer = Decimal(request.POST.get('offer', '0'))   
            except InvalidOperation:
                offer = Decimal('0')
                
            description = request.POST.get('description', '').strip()
            category_id = request.POST.get('category')
            Type_id = request.POST.get('Type')
            category = Categories.objects.get(id=category_id) if category_id else None
            Type = Types.objects.get(id=Type_id) if Type_id else None
            
            # Create the product
            product = Product.objects.create(
                name=product_name,
                description=description,
                original_price=price,
                offer=offer,
                category=category,
                Types=Type,
            )

            for size in size_data:
                size_stock = request.POST.get(f'stock_{size}')
                if size_stock:
                    try:
                        size_obj, created = Size.objects.get_or_create(name=size)
                        ProductSize.objects.create(product=product, size=size_obj, stock=int(size_stock))
                    except Size.DoesNotExist:
                        messages.error(request, f"Size '{size}' does not exist.")
                    except ValueError:
                        messages.error(request, f"Invalid stock value for size '{size}'.")            

            cropped_images_data = request.POST.get('cropped_images')
            if cropped_images_data:
                cropped_images = json.loads(cropped_images_data)
                for image_data in cropped_images:
                    image_content = ContentFile(base64.b64decode(image_data.split(",")[1]), name='product_image')
                    ProductImage.objects.create(product=product, image=image_content)

            return redirect('products:products_admin')

        elif action == "edit":
            product_id = request.POST.get("product_id")
            product = get_object_or_404(Product, id=product_id)
            product.name = request.POST.get("name")
            product.category_id = request.POST.get("category")
            product.Types_id = request.POST.get("Type")
            try:
                   product.original_price = Decimal(request.POST.get("price", '0') or '0')
            except InvalidOperation:
                product.original_price = Decimal('0')
        
            try:
                product.offer = Decimal(request.POST.get("offer", '0') or '0')
            except InvalidOperation:
                product.offer = Decimal('0')
                   
            product.description = request.POST.get("description", "").strip()
            product.save()
            if request.FILES.get('image'):
                 product_image = request.FILES['image']
                 product.image = product_image  
                 product.save()
            current_sizes = Size.objects.all()
            for size_obj in current_sizes:
                size_name = size_obj.name
                size_stock = request.POST.get(f'stock_{size_name}')
                if size_stock:
                    try:
                        product_size, created = ProductSize.objects.get_or_create(product=product, size=size_obj)
                        product_size.stock = int(size_stock)
                        product_size.save()
                    except ValueError:
                        messages.error(request, f"Invalid stock value for scale '{size_name}'.")
            
            messages.success(request, "Product updated successfully!")
            return redirect("products:products_admin")
        
        elif action == "toggle_status":
            product_id = request.POST.get("product_id")
            product = get_object_or_404(Product, id=product_id)
            product.status = "listed" if product.status == "dislisted" else "dislisted"
            product.save()
            messages.success(request, f"Product status changed to {product.status}!")
            return redirect("products:products_admin")
    
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', 'name')   
    sort_order = request.GET.get('sort_order', 'asc')   
    products = Product.objects.prefetch_related("category")
    
    if search_query:
        products = products.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
    
    if sort_by:
        if sort_order == 'asc':
            products = products.order_by(sort_by)
        else:
            products = products.order_by(f'-{sort_by}')
    
    paginator = Paginator(products, 5)   
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
  
    categories = Categories.objects.all().order_by("-id")
    types = Types.objects.all().order_by("-id")
    sizes = Size.objects.all()
    sizes_stock = {}
    for product in products:
        sizes_stock[product.id] = {}
        
        # Fetch the ProductSize objects directly from ProductSize model
        for product_size in ProductSize.objects.filter(product=product):
            sizes_stock[product.id][product_size.size.name] = product_size.stock

    for product in page_obj:
        product_sizes = ProductSize.objects.filter(product=product)
        total_stock = product_sizes.aggregate(Sum("stock"))["stock__sum"] or 0
        product.total_stock = total_stock
        product.size_stock = [{"size_name": ps.size.name, "stock": ps.stock} for ps in product_sizes]

    context = {
        'categories': categories,
        'types': types,
        'products': page_obj,   
        'sizes': sizes,
        'sizes_stock':sizes_stock,
        'search_query': search_query,
        'sort_by': sort_by,
        'sort_order': sort_order,
    }
    return render(request, 'products/products_admin.html', context)