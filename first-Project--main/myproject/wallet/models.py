from django.db import models
from django.contrib.auth import get_user_model



User = get_user_model()
 
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wallet of {self.user.username}"
    
    def add_funds(self, amount):
 
     if amount > 0:
        self.balance += amount
        self.save()  # Save the updated balance
       
        return True
      
     return False


# Transaction Model
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=20, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=[('Completed', 'Completed'), ('Pending', 'Pending')])
    transaction_type = models.CharField(max_length=20, choices=[('Credit', 'Credit'), ('Debit', 'Debit')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} for {self.user.username}"