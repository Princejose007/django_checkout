from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return self.name


class CartItem(models.Model):
    # Keeping your original field name to avoid breaking existing code
    user = models.ForeignKey(User,on_delete=models.CASCADE)

    cartproduct = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_cost(self):
        return self.quantity * self.cartproduct.price

    def __str__(self):
        return f"{self.quantity} of {self.cartproduct.name}"


class BillingDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)

    phone_number = models.CharField(max_length=15)
    Full_name = models.CharField(max_length=100)
    Address = models.TextField()

    def __str__(self):
        return f"{self.Full_name} ({self.phone_number})"


class Order(models.Model):
    # Link order to billing details instead of storing name/address separately
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)

    billing_details = models.ForeignKey(
        BillingDetails,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    order_date = models.DateTimeField(auto_now_add=True)

    # Totals from the cart at the time of purchase
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_quantity = models.PositiveIntegerField()

    status = models.CharField(max_length=50, default="Pending")

    def __str__(self):
        return f"Order {self.id} - {self.billing_details.Full_name} - {self.status}"


class OrderItem(models.Model):
    """
    Each OrderItem = one product inside an Order.
    These are created from CartItem when the user places the order.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    # Store price at the moment of order (if product price changes later, order remains correct)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_cost(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.quantity} x {self.product.name} for Order {self.order.id}"
    


from django.contrib.auth.models import User

class userprofile(models.Model):
        user=models.OneToOneField(User,on_delete=models.CASCADE)
        phone=models.CharField(max_length=12)
        address=models.TextField()
        def __str__(self):
            return self.username
