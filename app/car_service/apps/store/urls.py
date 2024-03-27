from django.urls import path, re_path

from car_service.apps.store import views

app_name = 'store'
urlpatterns = [
    path('categories/', views.category_list, name='category_list'),
    path('categories/<slug:slug>/', views.category_detail, name='category_detail'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart, name='cart'),
    path('api/cart/', views.cart_api, name='cart_api'),
    path('checkout/', views.checkout_view, name='checkout'),
]
