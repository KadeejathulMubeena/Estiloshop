from django.urls import path
from .  import views
urlpatterns = [
    path('',views.admin_home,name = "admin_home"),
    path('user_list/',views.user_list,name="user_list"),

    path('product_list/',views.product_list,name='admin_product_list'),
    path('edit_product/',views.edit_product,name='edit_product'),
    path('<int:id>/delete_product/',views.delete_product,name="delete_product"),
    path('add_product/',views.add_product,name="add_product"),
    path('soft_delete_product/<int:product_id>/',views.soft_delete_product,name="soft_delete_product"),
    path('list_product/<int:product_id>/',views.list_product,name="list_product"),

    path('add_category/',views.add_category,name="add_category"),
    path('admin_category_list/',views.admin_category_list,name='admin_category_list'),
    path('<int:id>/delete_category/',views.delete_category,name="delete_category"),
    path('admin/block_user/<int:user_id>/', views.block_user_admin, name='block_user'),
    path('admin/unblock_user/<int:user_id>/', views.unblock_user_admin, name='unblock_user'),
    path('admin/unlisted_category/<int:cat_id>/', views.unlisted_category, name='unlisted_category'),
    path('admin/listed_category/<int:cat_id>/', views.listed_category, name='listed_category'),
    
    path('variantion_list/',views.variation_list,name="variation_list"),
    path('<int:id>/delete_variant/',views.delete_variant,name="delete_variant"),
    path('add_product_attribute/',views.add_product_attribute,name="add_product_attribute"),
    path('listed_attribute/<int:attr_id>/',views.listed_attribute,name="listed_attribute"),
    path('unlisted_attribute/<int:attr_id>/',views.unlisted_attribute,name="unlisted_attribute"),

    path('add_size/',views.add_size, name="add_size"),
    path('add_color/',views.add_color, name="add_color"),
    path('size_color_list/', views.size_color_list, name="size_color"),

    path('product_images/',views.product_images_list,name='product_images_list'),
    path('add_images/', views.add_product_images, name='add_product_images'),
    path('<int:id>/delete_image/',views.delete_images,name="delete_images"),
    path('product_images/<int:product_id>/',views.product_images,name="product_images"),

    path('<int:category_id>/edit_category/',views.edit_category,name='edit_category'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('edit_variation/<int:variation_id>/', views.edit_variation, name='edit_variation'),
    
    path('add_brand/', views.add_brand, name="add_brand"),
    path('brand_list/', views.brand_list, name='brand_list'),
    path('edit_brand/<int:brand_id>/',views.edit_brand,name="edit_brand"),
    path('unlist_brand/<int:brand_id>/',views.unlist_brand,name="unlist_brand"),
    path('soft_delete_brand/<int:brand_id>/',views.soft_delete_brand, name="soft_delete_brand"),

    path('list_orders/',views.list_orders, name = "list_orders"),
    path('update_order_status/<int:order_id>/<str:status>/',views.update_order_status,name="update_order_status"),
    path('admin_order_details/<int:order_id>/',views.admin_order_details, name = "admin_order_details"),

    path('add_coupon/',views.add_coupon ,name="add_coupon"),
    path('coupon_list/',views.coupon_list , name="coupon_list"),
    path('unlist_coupon/<int:coupon_id>/',views.unlist_coupon,name = "unlist_coupon"),
    path('list_coupon/<int:coupon_id>/',views.list_coupon,name = "list_coupon"),
    path('delete_coupon/<int:coupon_id>/',views.delete_coupon,name="delete_coupon"),


    path('add_product_offer/',views.add_product_offer, name="add_product_offer"),
    path('product_offer_list/',views.product_offer_list, name="product_offer_list"),
    path('unlist_product_offer/<int:p_offer_id>/',views.unlist_product_offer,name = "unlist_product_offer"),
    path('list_product_offer/<int:p_offer_id>/',views.list_product_offer,name = "list_product_offer"),
    path('edit_product_offer/<int:p_offer_id>/',views.edit_product_offer,name="edit_product_offer"),

    path('add_category_offer/',views.add_category_offer, name="add_category_offer"),
    path('category_offer_list/',views.category_offer_list, name="category_offer_list"),
    path('unlist_category_offer/<int:cat_id>/',views.unlist_category_offer,name = "unlist_category_offer"),
    path('list_category_offer/<int:cat_id>/',views.list_category_offer,name = "list_category_offer"),
    path('edit_category_offer/<int:cat_offer_id>/',views.edit_category_offer,name="edit_category_offer"),
    

    path('show_sales_report/',views.show_sales_report,name="show_sales_report"),


]