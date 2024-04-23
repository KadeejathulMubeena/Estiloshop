from django.urls import path
from .  import views
urlpatterns = [
    path('',views.list_products ,name='shop'),
    path('category/<slug:category_slug>/',views.list_products ,name='products_by_category'),
    path('product/<slug:category_slug>/<slug:product_slug>/',views.product_detail, name='product_detail'),
    path('search/',views.search,name="search"),
    path('filter_products/',views.filter_products, name="filter_products"),
    path('shop_latest/',views.shop_latest,name="shop_latest"),
    path('add_wishlist/<int:product_id>/', views.add_wishlist , name="add_wishlist"),
    path('wishlist/', views.wishlist, name="wishlist"),
    path('delete_wishlist/<int:wishlist_id>/',views.delete_wishlist, name ="delete_wishlist"),
    path('get_available_colors/',views.get_available_colors,name="get_available_colors"),
    path('low_to_high/',views.low_to_high,name="low_to_high"),
    path('high_to_low/',views.high_to_low, name="high_to_low"),
]
