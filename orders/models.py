from django.db import models
from users.models import Users
from userpanel.models import Address
from product.models import ProductVariant


# Create your models here.


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Returned', 'Returned'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('CC', 'Credit Card'),
        ('RP', 'Razor Pay'),
        ('PP', 'PayPal'),
        ('BT', 'Bank Transfer'),
        ('COD', 'Cash on Delivery'),
    ]
    
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(choices=STATUS_CHOICES, max_length=20, default='Pending')
    payment_method = models.CharField(choices=PAYMENT_METHOD_CHOICES, max_length=20)
    payment_status = models.BooleanField(default=False)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='shipping_orders')
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    def calculate_total(self):
        self.subtotal = sum(item.price * item.quantity for item in self.items.all())
        self.total_amount = self.subtotal + self.shipping_cost - self.discount
        self.save()

    def __str__(self):
        return f"Order {self.order_number} by {self.user.email}"

class OrderItem(models.Model):
    CANCELLATION_REASON_CHOICES = [
        ('OPM', 'Order Placed by Mistake'),
        ('CMM', 'Changed My Mind'),
        ('DTL', 'Delivery Time Was Too Long'),
        ('ILN', 'Item No Longer Needed'),
        ('OWI', 'Ordered Wrong Item'),
        ('OFS', 'Item Not Available or Out of Stock'),
        ('DP', 'Received Damaged Product'),
        ('RII', 'Received Incorrect Item'),
        ('NME', 'Product Didn\'t Meet Expectations'),
        ('QC', 'Quality Concerns'),
        ('SCI', 'Size/Color Issue'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, related_name='order_items')
    quantity = models.PositiveIntegerField()
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cancellation_reason = models.CharField(choices=CANCELLATION_REASON_CHOICES, max_length=50, blank=True, null=True)
    custom_cancellation_reason = models.TextField(blank=True, null=True)
    note_admin = models.TextField(blank=True, null=True)
    is_cancelled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product_variant.product.name} - {self.quantity} pcs at ${self.price}"

    @property
    def total_price(self):
        return self.price * self.quantity
