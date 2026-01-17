from django.urls import path
from . import views

app_name = 'misc_pages'  

urlpatterns = [
    path('404/', views.custom_404, name='custom_404'),
]
