from django.db import models
from django.contrib.auth.models import AbstractUser,Group, Permission
from django.contrib.auth import get_user_model
# Create your models here.
class CustomUser(AbstractUser):
    profile_image = models.ImageField(upload_to='profile_images/',blank=True, null=True )
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',   
        blank=True,
    )
    
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',   
        blank=True,
    )
    
    def __str__(self):
        return self.username
    
User = get_user_model()


class Address(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    status  =models.CharField(default='listed')

    def full_address(self):
        """Returns the full address as a single string."""
        return f"{self.address_line1}, {self.address_line2 if self.address_line2 else ''}, {self.city}, {self.state} - {self.postal_code}, {self.country}"

    def __str__(self):
        return f"{self.address_line1}, {self.city}, {self.state} - {self.postal_code}"

    class Meta:
        verbose_name_plural = "Addresses"
        