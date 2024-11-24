from django.db import models
from users.models import Users


# Create your models here.


class Wallet(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='wallet', null=True, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s Wallet - Balance: {self.balance}"


class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("Cr", "Credit"),
        ("Dr", "Debit"),
    ]

    TRANSACTION_STATUS = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Failed", "Failed"),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS, default="Pending")
    transaction_id = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} - {self.amount}"
