from django.contrib import admin
from .models import CategoryOffer,Category,Brand

# Register your models here.
admin.site.register(CategoryOffer)
admin.site.register(Category)
admin.site.register(Brand)