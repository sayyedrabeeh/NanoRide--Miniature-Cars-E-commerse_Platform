from django.urls import path
from . import views

app_name = 'wallet'  

urlpatterns = [
     path('wallet/',views.wallet,name='wallet')
     
]
