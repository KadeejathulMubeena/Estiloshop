from django.db import models
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.utils import timezone


def validate_image(file):
    allowed_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
    return file.name.lower().endswith(allowed_extensions)

class Category(models.Model):
    category_name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='category')
    list = models.BooleanField(default = True)

    class Meta:
        ordering = ['category_name',]
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def get_url(self):
        return reverse_lazy('products_by_category', args=[self.slug])
    
    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.category_name)

        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.category_name

class Brand(models.Model):
    brand_name = models.CharField(max_length=100)
    brand_image = models.ImageField(upload_to='brand')
    soft_delete = models.BooleanField(default=False)

    def __str__(self):
        return self.brand_name    
    
class CategoryOffer(models.Model):
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank = True)
    discount_percentage = models.PositiveIntegerField(default=0)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    is_active = models.BooleanField(default = True)


    def __str__(self):
        return self.name


