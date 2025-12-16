# views.py - CÓDIGO COMPLETO CORREGIDO PARA CAFEITO
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Sum, Avg, Count
from django.http import JsonResponse
import time
import random
from datetime import datetime, timedelta
from .models import Category, Product, Order, OrderItem, InventoryLog
from .forms import RegisterForm, ProductForm

# ======================================== 
# FUNCIONES DE UTILIDAD
# ======================================== 
def is_admin(user):
    """Verifica si el usuario es administrador"""
    return user.is_staff or user.groups.filter(name='Administrador').exists()

def is_vendedor(user):
    """Verifica si el usuario es vendedor"""
    return user.groups.filter(name='Vendedor').exists()

def is_vendedor_or_admin(user):
    """Verifica si el usuario es vendedor o admin"""
    return is_admin(user) or is_vendedor(user)

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
    products = Product.objects.filter(category=category, is_active=True).order_by('tipo', 'name')
    
    # Obtener todas las categorías para la navegación rápida
    all_categories = Category.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'store/products.html', {
        'category': category,
        'products': products,
        'all_categories': all_categories
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
# SISTEMA DE PUNTO DE VENTA CON SESIÓN
# ======================================== 

def get_sale_session(request):
    """Obtiene los productos en la sesión de venta"""
    return request.session.get('sale_items', {})

def save_sale_session(request, sale_items):
    """Guarda los productos en la sesión de venta"""
    request.session['sale_items'] = sale_items
    request.session.modified = True

@user_passes_test(is_vendedor_or_admin)
def add_to_sale(request, product_id):
    """Agregar producto a la venta en sesión"""
    product = get_object_or_404(Product, id=product_id)
    
    # Obtener items de la sesión
    sale_items = get_sale_session(request)
    
    # Agregar o incrementar cantidad
    product_id_str = str(product_id)
    if product_id_str in sale_items:
        sale_items[product_id_str] += 1
    else:
        sale_items[product_id_str] = 1
    
    # Validar stock
    if sale_items[product_id_str] > product.stock:
        sale_items[product_id_str] = product.stock
        messages.warning(request, f'Solo hay {product.stock} unidades disponibles')
    else:
        messages.success(request, f'{product.name} agregado al resumen de venta')
    
    # Guardar en sesión
    save_sale_session(request, sale_items)
    
    # Redirigir a venta múltiple
    return redirect('multi_sale')

@login_required
def multi_sale(request):
    """Pantalla principal del punto de venta"""
    
    if request.method == 'POST':
        # Obtener items de la sesión
        sale_items = get_sale_session(request)
        
        # También procesar cantidades del formulario (por si se modificaron)
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                product_id = key.replace('quantity_', '')
                quantity = int(value) if value else 0
                
                if quantity > 0:
                    sale_items[product_id] = quantity
                elif product_id in sale_items:
                    del sale_items[product_id]
        
        # Guardar cambios en sesión
        save_sale_session(request, sale_items)
        
        # Procesar la venta
        payment_received = float(request.POST.get('payment_received', 0))
        
        # Calcular items y total
        items = []
        total = 0
        
        for product_id_str, quantity in sale_items.items():
            try:
                product = Product.objects.get(id=int(product_id_str))
                
                # Validar stock
                if quantity > product.stock:
                    messages.error(request, f'Solo hay {product.stock} unidades de {product.name}')
                    return redirect('multi_sale')
                
                subtotal = float(product.price) * quantity
                total += subtotal
                
                items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
            except Product.DoesNotExist:
                continue
        
        if not items:
            messages.error(request, 'No hay productos en la venta')
            return redirect('multi_sale')
        
        # Validar pago
        if payment_received < total:
            messages.error(request, 'El pago recibido es insuficiente')
            return redirect('multi_sale')
        
        # Calcular cambio
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
            notes=f'Pago: ${payment_received:.2f} | Cambio: ${change:.2f}'
        )
        
        # Crear items y actualizar stock
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['product'].price,
                subtotal=item['subtotal']
            )
            
            # Actualizar stock
            item['product'].stock -= item['quantity']
            item['product'].save()
            
            # Log de inventario
            InventoryLog.objects.create(
                product=item['product'],
                quantity_change=-item['quantity'],
                reason='Venta en punto de venta'
            )
        
        # Limpiar sesión
        request.session['sale_items'] = {}
        request.session.modified = True
        
        messages.success(request, f'¡Venta completada! Cambio: ${change:.2f} MXN')
        return redirect('sale_receipt', order_id=order.id)
    
    # Mostrar formulario de venta con productos en sesión
    sale_items = get_sale_session(request)
    
    categories = Category.objects.filter(is_active=True)
    categories_with_products = {}
    
    for category in categories:
        products_list = []
        products = Product.objects.filter(category=category, is_active=True, stock__gt=0)
        
        for product in products:
            product_dict = {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'stock': product.stock,
                'image': product.image.url if product.image else None,  # CORREGIDO
                'quantity': sale_items.get(str(product.id), 0)
            }
            products_list.append(product_dict)
        
        if products_list:
            categories_with_products[category.name] = products_list
    
    return render(request, 'store/multi_sale.html', {
        'categories_with_products': categories_with_products
    })

@login_required
def remove_from_sale(request, product_id):
    """Eliminar producto de la venta"""
    sale_items = get_sale_session(request)
    product = get_object_or_404(Product, id=product_id)
    
    if str(product_id) in sale_items:
        del sale_items[str(product_id)]
        save_sale_session(request, sale_items)
        messages.info(request, f'{product.name} eliminado de la venta')
    
    return redirect('multi_sale')

@login_required
def clear_sale(request):
    """Limpiar toda la venta"""
    request.session['sale_items'] = {}
    request.session.modified = True
    messages.info(request, 'Venta cancelada')
    return redirect('home')

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
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado')
            return redirect('admin_products')
    else:
        form = ProductForm()
    return render(request, 'store/admin_product_form.html', {'form': form})

@user_passes_test(is_admin)
def admin_product_edit(request, product_id):
    p = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=p)
        if form.is_valid():
            form.save()
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
        image = request.FILES.get('image')  # CORREGIDO: obtener archivo de imagen
        is_active = request.POST.get('is_active') == 'on'  # Checkbox
        
        category = Category.objects.create(
            name=name,
            description=description,
            is_active=is_active
        )
        
        # Guardar imagen si se proporcionó
        if image:
            category.image = image
            category.save()
        
        messages.success(request, 'Categoría creada exitosamente')
        return redirect('admin_categories')
    
    return render(request, 'store/admin_category_form.html')

@user_passes_test(is_admin)
def admin_category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        
        # Actualizar imagen solo si se proporciona una nueva
        image = request.FILES.get('image')
        if image:
            category.image = image
        
        category.is_active = request.POST.get('is_active') == 'on'
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
    """Reportes de ventas con filtros de fecha"""
    
    # Obtener fechas del filtro
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    
    # Fechas por defecto (últimos 7 días)
    today = timezone.now().date()
    
    if fecha_inicio_str:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_inicio = today - timedelta(days=7)
    else:
        fecha_inicio = today - timedelta(days=7)
    
    if fecha_fin_str:
        try:
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_fin = today
    else:
        fecha_fin = today
    
    # Permitir que fecha_inicio sea mayor que fecha_fin (intercambiarlas si es necesario)
    if fecha_fin < fecha_inicio:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio
    
    # Crear datetime para el inicio del día y fin del día
    fecha_inicio_dt = timezone.make_aware(datetime.combine(fecha_inicio, datetime.min.time()))
    fecha_fin_dt = timezone.make_aware(datetime.combine(fecha_fin, datetime.max.time()))
    
    # Filtrar órdenes por rango de fechas
    orders = Order.objects.filter(
        created_at__gte=fecha_inicio_dt,
        created_at__lte=fecha_fin_dt
    ).order_by('-created_at')
    
    # Calcular total
    total_ventas = orders.aggregate(Sum('total'))['total__sum'] or 0
    
    # Productos más vendidos en el rango
    productos_vendidos = OrderItem.objects.filter(
        order__created_at__gte=fecha_inicio_dt,
        order__created_at__lte=fecha_fin_dt
    ).values(
        'product__name', 
        'product__category__name'
    ).annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_qty')[:10]
    
    # Ventas por categoría
    ventas_por_categoria = OrderItem.objects.filter(
        order__created_at__gte=fecha_inicio_dt,
        order__created_at__lte=fecha_fin_dt
    ).values(
        'product__category__name'
    ).annotate(
        total_revenue=Sum('subtotal'),
        total_qty=Sum('quantity')
    ).order_by('-total_revenue')
    
    # Estadísticas adicionales
    total_ordenes = orders.count()
    ticket_promedio = total_ventas / total_ordenes if total_ordenes > 0 else 0
    
    # Calcular días del período
    dias_periodo = (fecha_fin - fecha_inicio).days + 1
    
    context = {
        'orders': orders,
        'total_ventas': total_ventas,
        'total_ordenes': total_ordenes,
        'ticket_promedio': ticket_promedio,
        'productos_vendidos': productos_vendidos,
        'ventas_por_categoria': ventas_por_categoria,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'dias_periodo': dias_periodo,
    }
    
    return render(request, 'store/reports.html', context)

# ======================================== 
# PANEL DE ADMINISTRACIÓN - USUARIOS
# ======================================== 
@user_passes_test(is_admin)
def admin_users(request):
    """Vista para gestionar usuarios"""
    users = User.objects.all().order_by('-date_joined')
    grupos = Group.objects.all()
    
    return render(request, 'store/admin_users.html', {
        'users': users,
        'grupos': grupos
    })

@user_passes_test(is_admin)
def admin_user_create(request):
    """Crear nuevo usuario"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        rol = request.POST.get('rol')
        
        # Validar que no exista el usuario
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe')
            return redirect('admin_user_create')
        
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Asignar rol
        if rol == 'admin':
            user.is_staff = True
            user.save()
            admin_group, created = Group.objects.get_or_create(name='Administrador')
            user.groups.add(admin_group)
        elif rol == 'vendedor':
            vendedor_group, created = Group.objects.get_or_create(name='Vendedor')
            user.groups.add(vendedor_group)
        
        messages.success(request, f'Usuario {username} creado exitosamente')
        return redirect('admin_users')
    
    return render(request, 'store/admin_user_form.html')

@user_passes_test(is_admin)
def admin_user_edit(request, user_id):
    """Editar usuario existente"""
    usuario = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        usuario.username = request.POST.get('username')
        usuario.email = request.POST.get('email')
        
        # Cambiar contraseña si se proporciona
        new_password = request.POST.get('password')
        if new_password:
            usuario.set_password(new_password)
        
        # Cambiar rol
        rol = request.POST.get('rol')
        usuario.groups.clear()
        
        if rol == 'admin':
            usuario.is_staff = True
            admin_group, created = Group.objects.get_or_create(name='Administrador')
            usuario.groups.add(admin_group)
        elif rol == 'vendedor':
            usuario.is_staff = False
            vendedor_group, created = Group.objects.get_or_create(name='Vendedor')
            usuario.groups.add(vendedor_group)
        
        usuario.save()
        messages.success(request, f'Usuario {usuario.username} actualizado')
        return redirect('admin_users')
    
    # Determinar rol actual
    rol_actual = 'vendedor'
    if usuario.is_staff or usuario.groups.filter(name='Administrador').exists():
        rol_actual = 'admin'
    
    return render(request, 'store/admin_user_form.html', {
        'usuario': usuario,
        'rol_actual': rol_actual
    })

@user_passes_test(is_admin)
def admin_user_delete(request, user_id):
    """Eliminar usuario"""
    usuario = get_object_or_404(User, id=user_id)
    
    # No permitir que se elimine a sí mismo
    if usuario.id == request.user.id:
        messages.error(request, 'No puedes eliminarte a ti mismo')
        return redirect('admin_users')
    
    username = usuario.username
    usuario.delete()
    messages.success(request, f'Usuario {username} eliminado')
    return redirect('admin_users')