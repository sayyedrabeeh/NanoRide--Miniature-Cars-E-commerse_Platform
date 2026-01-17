from django.urls import path
from . import views

app_name = 'reports'   

urlpatterns = [
    path('sales-report/', views.sales_report, name='sales_report'),
    path('download-report/<str:report_format>/', views.download_report, name='download_report'),
    
     path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

     
 ]
