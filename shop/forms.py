from django import forms
from .models import Product, ProductImage, Size, Color, ProductAttribute,ProductOffer
from django.core.exceptions import ValidationError
from category.models import Category,Brand


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'brand', 'material', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Product Name', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter Description', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'brand': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'material': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Material', 'required': True}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(list=True)
        self.fields['brand'].queryset = Brand.objects.filter(soft_delete = False) 
    
class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'product_attribute']
        widgets = {
            'product_attribute': forms.Select(attrs={'class': 'form-control', 'required': True}),
        }
       
class SizeForm(forms.ModelForm):
    class Meta:
        model = Size
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Size', 'required': True}),
        }


class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ['title', 'color_code']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Color', 'required': True}),
            'color_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Color Code', 'required': True}),
        }

class ProductAttributeForm(forms.ModelForm):
    class Meta:
        model = ProductAttribute
        fields = ['product', 'color', 'size', 'image', 'price', 'stock', 'is_available']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'color': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'size': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Price', 'required': True}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Stock', 'required': True}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProductOfferForm(forms.ModelForm):
    class Meta:
        model = ProductOffer
        fields = ['product', 'name', 'description', 'discount_percentage', 'end_date']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Offer Name', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter Offer Description'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Discount Percentage', 'required': True}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
        }
