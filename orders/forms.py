from django import forms
from .models import Order,Coupon

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_note','shipping_address', 'billing_address']


class PaymentForm(forms.Form):
    PAYMENT_METHOD_CHOICES = (
        ('COD', 'Cash on Delivery'),
        ('Online', 'Online Payment'),
    )
    payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES, widget=forms.RadioSelect)
    amount_paid = forms.DecimalField(label='Amount Paid')

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon 
        fields = [ 'discount', 'max_usage', 'minimum_amount','expiration_date']

class CancellationReasonForm(forms.ModelForm):
    class Meta:
        model = Order
        exclude = ['user', 'payment', 'order_number', 'user_profile', 'shipping_address', 'billing_address',
                   'order_note', 'order_total', 'tax', 'status', 'ip', 'is_ordered', 'coupon','return_reason', 'created_at',
                   'updated_at']
        
