from django.db import models
from shop.models import Product,ProductAttribute
from accounts.models import Account


# Create your models here.

    
class Cart(models.Model):
    cart_id=models.CharField(max_length=250,blank=True)
    date_added=models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id
    
class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE,null=True)
    product_attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE,null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,null=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE,null=True)
    quantity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        if self.product_attribute.offer_price :
            return self.product_attribute.offer_price * self.quantity
        else:
            return self.product_attribute.price * self.quantity
        
    
    def __str__(self):
        return f"{self.product_attribute.product.id} - {self.product_attribute.product.name} - {self.product_attribute.price} - {self.product_attribute.id}"
    

