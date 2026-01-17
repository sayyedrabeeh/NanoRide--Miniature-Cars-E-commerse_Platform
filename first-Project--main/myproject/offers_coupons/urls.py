from django.urls import path
from . import views

app_name = 'offers_coupons'  

urlpatterns = [
   path('coupon/',views.coupon,name='coupon'), 
   path('coupon/create/', views.coupon, name='create_coupon'),  # For creating a coupon
   path('coupon/edit/<int:coupon_id>/', views.coupon, name='edit_coupon'),
   path('listcoupon/<int:id>/',views.listcoupon,name='listcoupon')
]
