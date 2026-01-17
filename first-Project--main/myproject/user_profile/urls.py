from django.urls import path
from . import views

app_name = 'user_profile'  
urlpatterns = [
     path('users/',views.users,name='users'),
     path('address/',views.address,name='address'),
     path('blockuser/<int:id>',views.blockuser,name='blockuser'),
     path('listaddress/<int:id>/',views.listaddress,name='listaddress'),
     path('editaddress/<int:id>/',views.editaddress,name='editaddress'),
     path('profile/',views.profile,name='profile'),
     path('editprofile/',views.editprofile,name='editprofile'),
     path('change_password/',views.change_password,name='change_password'),



     
]
