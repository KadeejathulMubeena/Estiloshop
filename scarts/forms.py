from django import forms
from .models import Cart, CartItem

class CartForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = ['cart_id']

class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['product_attribute', 'quantity', 'cart', 'is_active']
        
