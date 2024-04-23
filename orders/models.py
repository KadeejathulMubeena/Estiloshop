from django.db import models
from accounts.models import Account,UserProfile,Address
from shop.models import Product, ProductAttribute
from django.utils import timezone
import secrets
import string
from datetime import date

# Create your models here.

class Payment(models.Model):
    PAYMENT_STATUS = (
        ('', ''),
        ('Pending', 'Pending'),
        ('Paid','Paid'),
        ('Failed','Failed'),
    )
    user = models.ForeignKey(Account, on_delete = models.CASCADE)
    payment_id = models.CharField(max_length = 100)
    payment_method = models.CharField(max_length=20)  
    amount_paid = models.PositiveIntegerField()
    status = models.CharField(max_length = 100,choices=PAYMENT_STATUS)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return self.payment_id
    

# Create your models here.
class Coupon(models.Model):
    coupon_code = models.CharField(max_length=50, unique=True)
    discount = models.PositiveIntegerField(default = 50)
    expiration_date = models.DateField()
    max_usage = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    minimum_amount = models.PositiveIntegerField(default=500)
    active = models.BooleanField(default = True)

    @staticmethod
    def generate_coupon_code(length=10):
        characters = string.ascii_letters + string.digits
        coupon_code = ''.join(secrets.choice(characters) for _ in range(length))
        return coupon_code.upper()
    
    def is_valid(self):
        return self.expiration_date >= date.today() and self.used_count < self.max_usage
    
    def is_used_by_user(self, user):
        redeemed_details = UserCoupons.objects.filter(coupon=self, user=user, is_used=True)
        return redeemed_details.exists()

    def __str__(self):
        return self.coupon_code

class UserCoupons(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=True)

    def __str__(self):
        return self.coupon.coupon_code

class Order(models.Model):
    STATUS = (
        ('Pending', 'Pending'),
        ('Accepted','Accepted'),
        ('Shipped','Shipped'),
        ('Out For Delivery','Out For Delivery'),
        ('Delivered','Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Returned','Returned')
    )

    CANCELLATION_REASONS = (
        ('No Longer Needed', 'No Longer Needed'),
        ('Ordered By Mistake', 'Ordered By Mistake'),
        ('Changed Mind', 'Changed Mind'),
        ('Found Better Price', 'Found Better Price'),
        ('Other', 'Other'),
    )

    user = models.ForeignKey(Account, on_delete = models.SET_NULL, null = True)
    payment = models.ForeignKey(Payment,on_delete = models.SET_NULL, null = True, blank = True)
    order_number = models.CharField(max_length = 20)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    shipping_address = models.ForeignKey(Address, related_name='shipping_address', on_delete=models.SET_NULL, null=True)
    billing_address = models.ForeignKey(Address, related_name='billing_address', on_delete=models.SET_NULL, null=True, blank=True)
    order_note = models.CharField(max_length = 100, blank = True)
    order_total = models.PositiveIntegerField()
    tax = models.PositiveIntegerField()
    status = models.CharField(max_length = 100 , choices = STATUS, default = 'Pending')
    ip = models.CharField(max_length = 10, blank = True)
    is_ordered = models.BooleanField(default = False)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    cancellation_reason = models.CharField(max_length=100, choices=CANCELLATION_REASONS, blank=True, null=True)
    return_reason = models.TextField(blank=True, null=True)


    def __str__(self):
        return self.user.first_name
    

class OrderProduct(models.Model):
    order = models.ForeignKey(Order,on_delete = models.CASCADE)
    payment = models.ForeignKey(Payment,on_delete = models.SET_NULL, blank = True, null = True)
    user = models.ForeignKey(Account,on_delete = models.CASCADE)
    product = models.ForeignKey(Product,on_delete = models.CASCADE)
    product_attribute = models.ForeignKey(ProductAttribute,on_delete = models.CASCADE)
    product_price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    ordered = models.BooleanField(default = False)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.product.name
    
class Wallet(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE, null=True)
    amount = models.PositiveIntegerField(default=100)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Wallet for User : {self.user.first_name}"
    
class WalletTransaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=255, choices=[('Credit', 'Credit'), ('Debit', 'Debit')])
    amount = models.PositiveIntegerField()
    transaction_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.wallet.user.first_name} - {self.transaction_type} - ${self.amount} - {self.transaction_date}"
 