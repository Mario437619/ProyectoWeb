from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.contrib import messages
from .models import Category, Product, Order, OrderItem, InventoryLog
from .forms import RegisterForm, ProductForm
import time, random
from django.db.models import Sum

def is_admin(user):
    return user.is_staff

def home(request):
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True)[:20]
    return render(request, 'store/home.html', {'categories': categories, 'products': products})

def products_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category, is_active=True)
    return render(request, 'store/category_products.html', {'category': category, 'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})

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

from django.contrib.auth import logout as auth_logout
def user_logout(request):
    auth_logout(request)
    return redirect('login')

# Cart (session-based)
def _get_cart(request):
    return request.session.setdefault('cart', {})

def add_to_cart(request, product_id):
    cart = _get_cart(request)
    qty = int(request.POST.get('qty', 1))
    cart[str(product_id)] = cart.get(str(product_id), 0) + qty
    request.session['cart'] = cart
    messages.success(request, 'Producto agregado al carrito')
    return redirect('cart')

def cart_view(request):
    cart = _get_cart(request)
    items = []
    total = 0
    for pid, qty in cart.items():
        p = Product.objects.get(id=int(pid))
        subtotal = float(p.price) * int(qty)
        items.append({'product': p, 'qty': qty, 'subtotal': subtotal})
        total += subtotal
    return render(request, 'store/cart.html', {'items': items, 'total': total})

def remove_from_cart(request, product_id):
    cart = _get_cart(request)
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    return redirect('cart')

@login_required
def checkout(request):
    cart = _get_cart(request)
    if not cart:
        messages.error(request, 'Carrito vacío')
        return redirect('home')

    if request.method == 'POST':
        order_number = f"ORD-{int(time.time()*1000)}-{random.randint(100,999)}"
        total = 0
        for pid, qty in cart.items():
            p = Product.objects.get(id=int(pid))
            total += float(p.price) * int(qty)

        now = timezone.now()
        order = Order.objects.create(order_number=order_number, customer=request.user, total=total,
                                     status='pending', payment_method='cash', payment_status='pending',
                                     created_at=now, updated_at=now)

        for pid, qty in cart.items():
            p = Product.objects.get(id=int(pid))
            qty_int = int(qty)
            subtotal = float(p.price) * qty_int
            OrderItem.objects.create(order=order, product=p, quantity=qty_int,
                                     unit_price=p.price, subtotal=subtotal, created_at=now)
            p.stock = p.stock - qty_int
            p.save()
            InventoryLog.objects.create(product=p, quantity_change=-qty_int, reason='Venta', created_at=now)

        request.session['cart'] = {}
        messages.success(request, f'Orden {order_number} creada correctamente')
        return redirect('home')

    return render(request, 'store/checkout.html')

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

@user_passes_test(is_admin)
def reports(request):
    today = timezone.now().date()
    orders_today = Order.objects.filter(created_at__date=today)
    total_today = orders_today.aggregate(Sum('total'))['total__sum'] or 0
    sold = OrderItem.objects.values('product__name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:10]
    return render(request, 'store/reports.html', {
        'orders_today': orders_today, 'total_today': total_today, 'sold': sold
    })
