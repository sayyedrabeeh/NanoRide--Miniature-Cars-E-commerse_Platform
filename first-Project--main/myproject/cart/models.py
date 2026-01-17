from django.db import models
from django.conf import settings
from products.models import Product,Size

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Store the discount applied

    def __str__(self):
        return f"Cart of {self.user.username}"

    def calculate_total(self):
        """
        Calculate the total price of all items in the cart before applying any discount.
        """
        return sum(item.item_total() for item in self.items.all())

    def calculate_discounted_total(self):
        """
        Calculate the total price after applying the discount.
        """
        total = self.calculate_total()
        return max(total - self.discount, 0)  # Ensure it doesn't go below zero


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE )
    size = models.ForeignKey(Size, on_delete=models.CASCADE)   

    quantity = models.PositiveIntegerField(default=1)

    def item_total(self):
        return self.product.price * self.quantity 


    def __str__(self):
        return f'{self.product.name} - {self.size.name} ({self.quantity})'
    