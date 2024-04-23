from django.contrib import admin
from . models import Product,ProductOffer,ProductAttribute,Size

# Register your models here.
admin.site.register(Product)
admin.site.register(ProductAttribute)
admin.site.register(ProductOffer)
admin.site.register(Size)