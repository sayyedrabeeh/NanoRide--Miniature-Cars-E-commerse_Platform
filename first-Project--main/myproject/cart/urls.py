from django.urls import path
from . import views

app_name = 'cart'  

urlpatterns = [
    path('cart/<str:action>/',views.cart_view,name='cart_view'),
    path('cart/',views.cart_view,name='cart_view'),
    path('payment/', views.payment, name='payment'),
    path('success/', views.success_page, name='success_page'),
    path('apply_coupon/', views.apply_coupon, name='apply_coupon'),

]
