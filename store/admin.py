from django.contrib import admin
from django.contrib import admin
from .models import Category, Product, Order, OrderItem, InventoryLog

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(InventoryLog)

# Register your models here.
