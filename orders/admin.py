from django.contrib import admin
from .models import Payment,Order,Wallet,Coupon
# Register your models here.
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'user', 'payment_method', 'amount_paid', 'status', 'created_at', 'updated_at']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.order_by('-updated_at')
        return queryset

admin.site.register(Payment, PaymentAdmin)
admin.site.register(Order)
admin.site.register(Wallet) 
admin.site.register(Coupon) 