from django.db import models
from app.models import Home
from django.contrib.auth.models import User

# Create your models here.


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Home, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ("PENDING_PAYMENT", "Pending payment"),
        ("PLACED", "Placed"),
        ("CONFIRMED", "Confirmed"),
        ("PACKED", "Packed"),
        ("SHIPPED", "Shipped"),
        ("OUT_FOR_DELIVERY", "Out for delivery"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    staus = models.CharField(max_length=30, choices=STATUS_CHOICES, default="PLACED")

    # delivery details (used by place_order)
    full_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=10, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=6, blank=True)
    payment_method = models.CharField(max_length=20, default="COD")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} : {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    product = models.ForeignKey(Home, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)


class OrderTracking(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tracking")

    status = models.CharField(max_length=30)

    desription = models.CharField(max_length=225, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class Payment(models.Model):

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="payment"
    )

    razorpay_order_id = models.CharField(max_length=225)

    razorpay_signature = models.CharField(max_length=10, blank=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=30, default="PENDING")

    created_at = models.DateTimeField(auto_now_add=True)
