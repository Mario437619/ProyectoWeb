from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('category/<int:category_id>/', views.products_by_category, name='products_by_category'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),

    path('admin/products/', views.admin_products, name='admin_products'),
    path('admin/products/create/', views.admin_product_create, name='admin_product_create'),
    path('admin/products/<int:product_id>/edit/', views.admin_product_edit, name='admin_product_edit'),
    path('admin/products/<int:product_id>/delete/', views.admin_product_delete, name='admin_product_delete'),

    path('admin/reports/', views.reports, name='reports'),
]
