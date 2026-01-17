from django.shortcuts import render

# Create your views here.
def custom_404(request):
    return render(request,'misc_pages/404.html')