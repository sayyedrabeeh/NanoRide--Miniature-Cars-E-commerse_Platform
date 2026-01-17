from django.db import models
from user_profile.models import CustomUser
from user_profile.models import Address
import uuid
from django.utils import timezone
from datetime import timedelta
from products.models import Size


# Create your models here.
class Order(models.Model):
    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('RazorPay', 'Razor Pay'),
        ('Wallet', 'Wallet')
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failure', 'Failure')
    ]

    order_id = models.AutoField(primary_key=True)  
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tracking_number = models.CharField(max_length=20, unique=True, editable=False)
    shipping_address = models.ForeignKey(Address, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    coupon_used = models.BooleanField(default=False)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    payment=models.CharField(max_length=20,default='Failure')
    estimated_delivery_date = models.DateField(blank=True, null=True)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Order {self.order_id} by {self.user.username}'

    def save(self, *args, **kwargs):
         
        if not self.tracking_number:
            self.tracking_number = str(uuid.uuid4().hex[:8])
        if not self.estimated_delivery_date:
            self.estimated_delivery_date = timezone.now().date() + timedelta(days=3)   
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    STATUS_CHOICES = [
        ("Order Pending", "Order Pending"),
        ("Order Confirmed", "Order Confirmed"),
        ("Shipped", "Shipped"),
        ("Out For Delivery", "Out For Delivery"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
        ("Requested Return", "Requested Return"),
        ("Approve Returned", "Approve Returned"),
        ("Reject Returned", "Reject Returned"),
    ]
    
    orderitem_id = models.AutoField(primary_key=True)  
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    quantity = models.FloatField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.ForeignKey(Size, related_name='order_items', on_delete=models.CASCADE, default=1)   
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Order Pending') 
    subtotal_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    return_reason = models.TextField(blank=True, null=True)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE) 
    