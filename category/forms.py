from django import forms
from . models import Category, Brand,CategoryOffer
from django.core.exceptions import ValidationError

    
class CategoryForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = ['category_name', 'description', 'image']

        widgets = {
            'category_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Category Name', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter Category Description'}),
        }

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['brand_name', 'brand_image']
        widgets = {
            'brand_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Brand Name', 'required': True}),
        }

class CategoryOfferForm(forms.ModelForm):
    class Meta:
        model = CategoryOffer
        fields = ['category','name','description', 'discount_percentage','end_date']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Offer Name', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter Offer Description'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Discount Percentage', 'required': True}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
        }