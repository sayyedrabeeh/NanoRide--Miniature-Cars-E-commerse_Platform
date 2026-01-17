from django.db import models
from products.models import Product
from django.conf import settings

# Create your models here.
 
 

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.PositiveIntegerField()   
    status = models.CharField(max_length=10, default='listed')  
    max_uses = models.PositiveIntegerField(default=100)   
    used_count = models.PositiveIntegerField(default=0)  
 
    def __str__(self):
        return self.code

    def is_active(self):
        return self.status == 'listed' and self.used_count < self.max_uses

    def can_be_used_by(self, user):
       
        return not CouponUsage.objects.filter(user=user, coupon=self).exists()
    
class CouponUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'coupon')   

    def __str__(self):
        return f'{self.user} used {self.coupon.code} at {self.used_at}'