from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.core.validators import MinLengthValidator


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.is_active = False  # Set is_active to False by default
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


class Account(AbstractUser):
    first_name=models.CharField(max_length=50)
    last_name=models.CharField(max_length=50)
    email=models.EmailField(max_length=100,unique=True)
    username=models.CharField(max_length=50,unique=True)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add = True)

    USERNAME_FIELD='email'
    REQUIRED_FIELDS=['username']
    objects=CustomUserManager()

    def full_name(self):
        return f"{self.first_name.capitalize()} {self.last_name.capitalize()}"
    
    def __str__(self):
        return self.username
    
class UserProfile(models.Model):
    user = models.OneToOneField(Account, on_delete = models.CASCADE)
    profile_picture = models.ImageField(blank = True, upload_to ='profile_picture')
    phone = models.CharField(max_length = 20,blank = True)
  
    def __str__(self):
        return self.user.first_name    


class State(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class District(models.Model):
    name = models.CharField(max_length=50)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class Address(models.Model):
    
    user= models.ForeignKey(Account, on_delete=models.CASCADE)
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=50, default='India')
    state = models.ForeignKey(State, on_delete=models.SET_NULL, blank = True, null = True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, blank = True, null = True)
    postal_code = models.CharField(max_length=20)

    def full_address(self):
        return f"{self.address_line_1} {self.address_line_2},{self.country}, {self.state},{self.district}, {self.postal_code}"

    def __str__(self):
        return f"{self.address_line_1}, {self.district}, {self.state}, {self.country}"

