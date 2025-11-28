from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.single_product, name='single_product'),

    path('cart/', views.cart_view, name='cart_view'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart_update/<int:cart_id>/', views.cart_update, name='cart_update'),
    path('remove_cart/<int:cart_id>/', views.remove_cart, name='remove_cart'),

    path('checkout/', views.checkout, name='checkout'),
    path('order_confirmation/', views.order_confirmation, name='order_confirmation'),

    # Razorpay callback
    path('payment-success/', views.payment_success, name='payment_success'),
    path('register_view/', views.register_view, name='register_view'), 
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.log_out_view, name='log_out_view'),
    path('order_history/', views.order_history, name='order_history'),
]
