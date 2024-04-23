from django.urls import path
from .  import views
urlpatterns = [
    path('place_order/', views.place_order, name = "place_order"),
    path('order_complete/', views.order_complete, name='order_complete'),
    path('cash_on_delivery/<int:order_number>',views.cash_on_delivery, name="cash_on_delivery"),
    path('apply_coupon/',views.apply_coupon, name = "apply_coupon"),
    path('remove_coupon/', views.remove_coupon, name='remove_coupon'),
    path('confirm_razorpay_payment/<int:order_number>/',views.confirm_razorpay_payment,name="confirm_razorpay_payment"),
    path('failed_payment/<int:order_number>/',views.failed_payment,name="failed_payment"),
    path('continue_payment/<int:order_number>/',views.continue_payment,name="continue_payment"),
    path('payment_with_wallet/<int:order_number>',views.payment_with_wallet, name = "payment_with_wallet" ),
    path('order_confirmed/<int:order_number>/', views.order_confirmed, name='order_confirmed'),
    path('order_invoice/<int:order_id>',views.order_invoice,name="order_invoice"),
    path('payments/<int:order_id>/', views.payments, name='payments'),
]