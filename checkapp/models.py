from django.db import models


# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return self.name
    


class CartItem(models.Model):
        cartproduct = models.ForeignKey(Product, on_delete=models.CASCADE)
        quantity = models.PositiveIntegerField(default=1)


        @property
        def total_cost(self):
            return self.quantity * self.cartproduct.price
        


        def __str__(self):
            return f"{self.quantity} of {self.cartproduct.name}"
        

class BillingDetails(models.Model):
     phone_number = models.CharField(max_length=15)
     Full_name = models.CharField(max_length=100)
     Address = models.TextField()




class Order(models.Model):
     user_name = models.CharField(max_length=100)
     order_date = models.DateTimeField(auto_now_add=True)
     product_id = models.IntegerField()   
     total_price = models.DecimalField(max_digits=10, decimal_places=2)
     total_quantity = models.PositiveIntegerField()
     Delivery_address = models.CharField(max_length=255)
     status = models.CharField(max_length=50)
     def __str__(self):
          return f"Order {self.id} by {self.status}"
     

class orderItem(models.Model):
     order = models.ForeignKey(Order, on_delete=models.CASCADE)
     product = models.ForeignKey(Product, on_delete=models.CASCADE)
     quantity = models.PositiveIntegerField()
     price = models.DecimalField(max_digits=10, decimal_places=2)

     def __str__(self):
          return f"{self.quantity} of {self.product.name} in Order {self.order.id}"
     