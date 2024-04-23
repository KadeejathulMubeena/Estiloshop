from django.urls import path
from .  import views
urlpatterns = [
    path('register/',views.register ,name='register'),
    path('login/',views.log_in ,name='login'),
    path('logout/',views.log_out ,name='logout'),
    path('', views.dashboard, name = "dashboard"),

    path('activate/<str:uidb64>/<str:token>/',views.activate,name="activate"),
    path('forgotpassword/',views.forgotpassword,name='forgotpassword'),
    path('resetpassword/<str:uidb64>/<str:token>/', views.resetpassword_validate, name="resetpassword_validate"),
    path('resetpassword/',views.resetpassword,name='resetpassword'),

    path('my_orders/',views.my_orders, name = "my_orders"),
    path('edit_profile/',views.edit_profile, name = "edit_profile"),
    path('change_password/', views.change_password, name = "change_password"),
    path('order_detail/<int:order_id>/',views.order_detail, name="order_detail"),
    path('cancel_order/<int:order_id>/',views.cancel_order,name="cancel_order_confirmation"),
    path('return_order/<int:order_id>/',views.return_order, name="return_order"),

    path('add_address/', views.add_address, name="add_address"),
    path('ajax_load_district',views.ajax_load_district, name ='ajax_load_district'),
    path('edit_address/<int:address_id>/', views.edit_address, name="edit_address"),
    path('delete_address/<int:address_id>/', views.delete_address, name="delete_address"),

    path('wallet/',views.wallet, name = "wallet"),
    path('wallet/wallet_transaction/',views.wallet_transaction,name = "wallet_transaction")
 

]
