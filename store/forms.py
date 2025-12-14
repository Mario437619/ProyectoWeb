from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Product

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)
    
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

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
    
    tipo = forms.ChoiceField(choices=TIPO_CHOICES, required=False, label='Tipo de Producto')
    
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'tipo', 'price', 'image_url', 'stock', 'is_active']