from django.urls import path
from . import views

app_name = 'products'  

urlpatterns = [
    path('',views.home,name='home'),
    path('brand_products/<str:brand_name>/',views.brand_products,name='brand_products'),
    path('catogery/',views.catogery,name='catogery'),
    path('Type/',views.Type,name='Type'),
    path('products_detail/<int:id>',views.products_detail,name='products_detail'),
    path('products/',views.products,name='products'),
    path('products_admin/',views.products_admin,name='products_admin'),
    path('wishlist/<str:action>/', views.wishlist, name='wishlist'),
    path('wishlist/<str:action>/<int:product_id>/', views.wishlist, name='wishlist'),
 
]
