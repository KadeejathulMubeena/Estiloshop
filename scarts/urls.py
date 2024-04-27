from django.urls import path
from .  import views
urlpatterns = [
    path('',views.cart ,name='cart'),
    path('add_cart/<int:product_id>',views.add_to_cart,name='add_cart'),
    path('remove_cart/<int:product_attribute_id>/<int:cart_item_id>/',views.remove_cart,name='remove_cart'),
    path('remove_cart_item/<int:product_attribute_id>/<int:cart_item_id>/',views.remove_cart_item,name='remove_cart_item'),
    path('increase_quantity/<int:cart_item_id>/', views.increase_quantity, name='increase_quantity'),
    path('checkout/', views.checkout, name = 'checkout'),
]