from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Product

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'})
    )
    
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        labels = {
            'username': 'Nombre de Usuario',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Contraseña'
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
        self.fields['password1'].help_text = 'Mínimo 8 caracteres'
        
        self.fields['password2'].label = 'Confirmar Contraseña'
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar contraseña'})
        self.fields['password2'].help_text = 'Ingresa la misma contraseña'
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso')
        return username
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Las contraseñas no coinciden')
        return password2


class ProductForm(forms.ModelForm):
    TIPO_CHOICES = [
        ('', '-- Sin clasificar --'),
        ('Bebida Caliente', 'Bebida Caliente'),
        ('Bebida Fría', 'Bebida Fría'),
        ('Pan Dulce', 'Pan Dulce'),
        ('Pan Salado', 'Pan Salado'),
        ('Pastel Individual', 'Pastel Individual'),
        ('Pastel Grande', 'Pastel Grande'),
    ]
    
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES, 
        required=False, 
        label='Tipo de Producto',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'tipo', 'price', 'image', 'stock', 'is_active']
        labels = {
            'name': 'Nombre del Producto',
            'description': 'Descripción',
            'category': 'Categoría',
            'price': 'Precio (MXN)',
            'image': 'Imagen del Producto',
            'stock': 'Cantidad en Stock',
            'is_active': 'Activo',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Café Americano'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del producto...'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price <= 0:
            raise forms.ValidationError('El precio debe ser mayor a 0')
        return price
    
    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock and stock < 0:
            raise forms.ValidationError('El stock no puede ser negativo')
        return stock