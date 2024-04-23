from django.db import models
from category.models import Category,Brand,CategoryOffer
from django.urls import reverse
from django.utils.text import slugify
from django.db.models import Sum
from django.utils import timezone

# Create your models here.

class Product(models.Model):
  
    name = models.CharField(max_length=250, null=True)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE , null= True)
    material = models.CharField(max_length=250, blank = True)
    is_available = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def get_url(self): 
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class ProductOffer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank = True)
    discount_percentage = models.PositiveIntegerField(default=0)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    is_active = models.BooleanField(default = True)


    def __str__(self):
        return self.name


class Size(models.Model):
    title=models.CharField(max_length=100, unique = True)

    def __str__(self):
        return self.title
    
class Color(models.Model):
    title=models.CharField(max_length=100, unique = True)
    color_code=models.CharField(max_length=100, unique = True)

    def __str__(self):
        return self.title
    
class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product')
    price = models.PositiveIntegerField()
    stock = models.PositiveIntegerField() 
    is_available = models.BooleanField(default=True)
    offer_price = models.PositiveIntegerField(blank = True,null = True)
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)


    def total_quantity_sold(self):
        from orders.models import OrderProduct

        # Aggregate the total quantity sold for this product attribute
        total_sold = OrderProduct.objects.filter(product_attribute=self, ordered=True).aggregate(total_quantity=Sum('quantity'))
        return total_sold['total_quantity'] or 0  # Return 0 if no sales recorded
    
    def calculate_discounted_price(self):
        product_offer = ProductOffer.objects.filter(product=self.product, is_active=True).first()
        product_discount = 0  

        if product_offer:
            product_discount = product_offer.discount_percentage

        category_offer = CategoryOffer.objects.filter(category=self.product.category, is_active=True).first()
        category_discount = 0 

        if category_offer:
            category_discount = category_offer.discount_percentage

        discount_percentage = max(product_discount, category_discount)

        if discount_percentage > 0:
            discount_amount_paise = int(self.price * (discount_percentage / 100) * 100)

            discount_amount = discount_amount_paise // 100
            final_price = self.price - discount_amount

            # Set offer_price to the discounted price
            self.offer_price = final_price
        else:
            # No active offer, set offer_price to None
            self.offer_price = None
            final_price = self.price

        # Save the changes to the ProductAttribute instance
        self.save()
        return {
                'final_price': final_price,
                'discount_percentage': discount_percentage,
                'product_offer': product_offer,
                'category_offer': category_offer
            }

    @property
    def multiple_images(self):
        return self.p_images.all()
       
    def __str__(self):
        return self.product.name
    
class ProductImage(models.Model):
  image = models.ImageField(upload_to='product-image')
  product_attribute = models.ForeignKey(ProductAttribute, related_name="p_images", on_delete=models.SET_NULL, null=True)
  date = models.DateTimeField(auto_now_add=True)

  class Meta:
    verbose_name_plural = 'Product Images'

from accounts.models import Account

class Wishlist(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    items = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    cerated_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f"Wishlist of {self.user.first_name}"