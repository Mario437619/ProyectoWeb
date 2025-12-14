# views.py - CÓDIGO COMPLETO PARA CAFEITO

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
import time
import random

from .models import Category, Product, Order, OrderItem, InventoryLog
from .forms import RegisterForm, ProductForm


# ========================================
# FUNCIONES DE UTILIDAD
# ========================================

def is_admin(user):
    return user.is_staff


# ========================================
# VISTAS PÚBLICAS
# ========================================

def home(request):
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True)[:20]
    return render(request, 'store/home.html', {
        'categories': categories, 
        'products': products
    })


def products_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category, is_active=True)
    return render(request, 'store/category_products.html', {
        'category': category, 
        'products': products
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})


# ========================================
# AUTENTICACIÓN
# ========================================

def user_register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Cuenta creada. Ingresa ahora.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'store/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'store/login.html', {'form': form})


def user_logout(request):
    auth_logout(request)
    return redirect('login')


# ========================================
# BÚSQUEDA DE PRODUCTOS
# ========================================

def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(is_active=True)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    return render(request, 'store/search_results.html', {
        'products': products, 
        'query': query
    })


# ========================================
# SISTEMA DE VENTA RÁPIDA (SIN CARRITO)
# ========================================

@login_required
def quick_sale(request, product_id):
    """Vista para venta rápida de un producto"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        payment_received = float(request.POST.get('payment_received', 0))
        
        # Calcular totales
        subtotal = float(product.price) * quantity
        total = subtotal
        change = payment_received - total
        
        # Validar stock
        if quantity > product.stock:
            messages.error(request, f'Solo hay {product.stock} unidades disponibles')
            return redirect('quick_sale', product_id=product_id)
        
        # Validar pago
        if payment_received < total:
            messages.error(request, 'El pago recibido es insuficiente')
            return redirect('quick_sale', product_id=product_id)
        
        # Crear orden
        now = timezone.now()
        order_number = f"ORD-{int(time.time()*1000)}-{random.randint(100,999)}"
        
        order = Order.objects.create(
            order_number=order_number,
            customer=request.user,
            total=total,
            status='completed',
            payment_method='cash',
            payment_status='completed',
            created_at=now,
            updated_at=now
        )
        
        # Crear item de orden
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            unit_price=product.price,
            subtotal=subtotal,
            created_at=now
        )
        
        # Actualizar stock
        product.stock -= quantity
        product.save()
        
        # Log de inventario
        InventoryLog.objects.create(
            product=product,
            quantity_change=-quantity,
            reason='Venta directa',
            created_at=now
        )
        
        messages.success(request, f'¡Venta completada! Cambio: ${change:.2f} MXN')
        return redirect('sale_receipt', order_id=order.id)
    
    return render(request, 'store/quick_sale.html', {'product': product})


@login_required
def sale_receipt(request, order_id):
    """Vista para mostrar el ticket de venta"""
    order = get_object_or_404(Order, id=order_id)
    items = OrderItem.objects.filter(order=order)
    return render(request, 'store/sale_receipt.html', {
        'order': order, 
        'items': items
    })


# ========================================
# HISTORIAL DE ÓRDENES DEL USUARIO
# ========================================

@login_required
def user_orders(request):
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'store/user_orders.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    items = OrderItem.objects.filter(order=order)
    return render(request, 'store/order_detail.html', {
        'order': order, 
        'items': items
    })


# ========================================
# PANEL DE ADMINISTRACIÓN - DASHBOARD
# ========================================

@user_passes_test(is_admin)
def admin_dashboard(request):
    today = timezone.now().date()
    
    # Estadísticas generales
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_customers = Order.objects.values('customer').distinct().count()
    
    # Ventas del mes
    month_start = today.replace(day=1)
    monthly_sales = Order.objects.filter(
        created_at__gte=month_start
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Ventas de hoy
    daily_sales = Order.objects.filter(
        created_at__date=today
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Productos con poco stock
    low_stock = Product.objects.filter(
        stock__lt=10, 
        is_active=True
    ).order_by('stock')[:10]
    
    # Últimas órdenes
    recent_orders = Order.objects.order_by('-created_at')[:10]
    
    # Productos más vendidos
    top_products = OrderItem.objects.values(
        'product__name'
    ).annotate(
        total_qty=Sum('quantity')
    ).order_by('-total_qty')[:10]
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'monthly_sales': monthly_sales,
        'daily_sales': daily_sales,
        'low_stock': low_stock,
        'recent_orders': recent_orders,
        'top_products': top_products,
    }
    
    return render(request, 'store/admin_dashboard.html', context)


# ========================================
# PANEL DE ADMINISTRACIÓN - PRODUCTOS
# ========================================

@user_passes_test(is_admin)
def admin_products(request):
    products = Product.objects.all()
    return render(request, 'store/admin_products.html', {'products': products})


@user_passes_test(is_admin)
def admin_product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            now = timezone.now()
            p.created_at = now
            p.updated_at = now
            p.save()
            messages.success(request, 'Producto creado')
            return redirect('admin_products')
    else:
        form = ProductForm()
    return render(request, 'store/admin_product_form.html', {'form': form})


@user_passes_test(is_admin)
def admin_product_edit(request, product_id):
    p = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=p)
        if form.is_valid():
            p = form.save(commit=False)
            p.updated_at = timezone.now()
            p.save()
            messages.success(request, 'Producto actualizado')
            return redirect('admin_products')
    else:
        form = ProductForm(instance=p)
    return render(request, 'store/admin_product_form.html', {'form': form})


@user_passes_test(is_admin)
def admin_product_delete(request, product_id):
    p = get_object_or_404(Product, id=product_id)
    p.delete()
    messages.success(request, 'Producto eliminado')
    return redirect('admin_products')


# ========================================
# PANEL DE ADMINISTRACIÓN - CATEGORÍAS
# ========================================

@user_passes_test(is_admin)
def admin_categories(request):
    categories = Category.objects.all()
    return render(request, 'store/admin_categories.html', {
        'categories': categories
    })


@user_passes_test(is_admin)
def admin_category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        image_url = request.POST.get('image_url')
        now = timezone.now()
        
        Category.objects.create(
            name=name,
            description=description,
            image_url=image_url,
            is_active=True,
            created_at=now,
            updated_at=now
        )
        messages.success(request, 'Categoría creada exitosamente')
        return redirect('admin_categories')
    
    return render(request, 'store/admin_category_form.html')


@user_passes_test(is_admin)
def admin_category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        category.image_url = request.POST.get('image_url')
        category.updated_at = timezone.now()
        category.save()
        messages.success(request, 'Categoría actualizada')
        return redirect('admin_categories')
    
    return render(request, 'store/admin_category_form.html', {
        'category': category
    })


@user_passes_test(is_admin)
def admin_category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    messages.success(request, 'Categoría eliminada')
    return redirect('admin_categories')


# ========================================
# PANEL DE ADMINISTRACIÓN - ÓRDENES
# ========================================

@user_passes_test(is_admin)
def admin_orders(request):
    status_filter = request.GET.get('status', '')
    orders = Order.objects.all().order_by('-created_at')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    return render(request, 'store/admin_orders.html', {'orders': orders})


@user_passes_test(is_admin)
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = OrderItem.objects.filter(order=order)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        order.status = new_status
        order.updated_at = timezone.now()
        order.save()
        messages.success(request, f'Orden actualizada a {new_status}')
        return redirect('admin_orders')
    
    return render(request, 'store/admin_order_detail.html', {
        'order': order, 
        'items': items
    })


# ========================================
# REPORTES
# ========================================

@user_passes_test(is_admin)
def reports(request):
    today = timezone.now().date()
    orders_today = Order.objects.filter(created_at__date=today)
    total_today = orders_today.aggregate(Sum('total'))['total__sum'] or 0
    
    sold = OrderItem.objects.values('product__name').annotate(
        total_qty=Sum('quantity')
    ).order_by('-total_qty')[:10]
    
    return render(request, 'store/reports.html', {
        'orders_today': orders_today,
        'total_today': total_today,
        'sold': sold
    })
# ========================================
# AGREGAR ESTAS FUNCIONES A views.py
# ========================================

@login_required
def multi_sale(request):
    """Vista para venta de múltiples productos"""
    products = Product.objects.filter(is_active=True, stock__gt=0)
    
    if request.method == 'POST':
        # Obtener productos seleccionados
        selected_products = []
        total = 0
        
        for product in products:
            quantity_key = f'quantity_{product.id}'
            quantity = int(request.POST.get(quantity_key, 0))
            
            if quantity > 0:
                if quantity > product.stock:
                    messages.error(request, f'{product.name}: Solo hay {product.stock} unidades disponibles')
                    return redirect('multi_sale')
                
                subtotal = float(product.price) * quantity
                selected_products.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
                total += subtotal
        
        if not selected_products:
            messages.error(request, 'Debes seleccionar al menos un producto')
            return redirect('multi_sale')
        
        # Obtener pago recibido
        payment_received = float(request.POST.get('payment_received', 0))
        
        if payment_received < total:
            messages.error(request, 'El pago recibido es insuficiente')
            return redirect('multi_sale')
        
        change = payment_received - total
        
        # Crear orden
        now = timezone.now()
        order_number = f"ORD-{int(time.time()*1000)}-{random.randint(100,999)}"
        
        order = Order.objects.create(
            order_number=order_number,
            customer=request.user,
            total=total,
            status='completed',
            payment_method='cash',
            payment_status='completed',
            created_at=now,
            updated_at=now
        )
        
        # Crear items y actualizar stock
        for item in selected_products:
            product = item['product']
            quantity = item['quantity']
            subtotal = item['subtotal']
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.price,
                subtotal=subtotal,
                created_at=now
            )
            
            # Actualizar stock
            product.stock -= quantity
            product.save()
            
            # Log de inventario
            InventoryLog.objects.create(
                product=product,
                quantity_change=-quantity,
                reason='Venta múltiple',
                created_at=now
            )
        
        messages.success(request, f'¡Venta completada! Cambio: ${change:.2f} MXN')
        return redirect('sale_receipt', order_id=order.id)
    
    # Agrupar productos por categoría
    categories_with_products = {}
    for product in products:
        category_name = product.category.name
        if category_name not in categories_with_products:
            categories_with_products[category_name] = []
        categories_with_products[category_name].append(product)
    
    return render(request, 'store/multi_sale.html', {
        'categories_with_products': categories_with_products,
        'all_products': products
    })