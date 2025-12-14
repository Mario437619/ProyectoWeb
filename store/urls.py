# urls.py - COMPLETO Y ACTUALIZADO

from django.urls import path
from . import views

urlpatterns = [
    # Páginas principales
    path('', views.home, name='home'),
    path('search/', views.search_products, name='search_products'),
    
    # Autenticación
    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Productos
    path('category/<int:category_id>/', views.products_by_category, name='products_by_category'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    
    # VENTA RÁPIDA (sin carrito)
    path('sale/<int:product_id>/', views.quick_sale, name='quick_sale'),
    path('receipt/<int:order_id>/', views.sale_receipt, name='sale_receipt'),
    
    # Órdenes de usuario
    path('my-orders/', views.user_orders, name='user_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Admin - Dashboard
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Admin - Productos
    path('admin/products/', views.admin_products, name='admin_products'),
    path('admin/products/create/', views.admin_product_create, name='admin_product_create'),
    path('admin/products/edit/<int:product_id>/', views.admin_product_edit, name='admin_product_edit'),
    path('admin/products/delete/<int:product_id>/', views.admin_product_delete, name='admin_product_delete'),
    
    # Admin - Categorías
    path('admin/categories/', views.admin_categories, name='admin_categories'),
    path('admin/categories/create/', views.admin_category_create, name='admin_category_create'),
    path('admin/categories/edit/<int:category_id>/', views.admin_category_edit, name='admin_category_edit'),
    path('admin/categories/delete/<int:category_id>/', views.admin_category_delete, name='admin_category_delete'),
    
    # Admin - Órdenes
    path('admin/orders/', views.admin_orders, name='admin_orders'),
    path('admin/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    
    # Reportes
    path('admin/reports/', views.reports, name='reports'),
]