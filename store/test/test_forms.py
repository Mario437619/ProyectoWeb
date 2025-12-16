from django.test import TestCase
from store.forms import ProductForm
from store.models import Category

class ProductFormTest(TestCase):
    
    def test_form_valid_data(self):
        """Test que el form acepta datos válidos"""
        category = Category.objects.create(name="Test")
        
        # CORREGIDO: Agregados todos los campos requeridos
        form = ProductForm(data={
            'name': 'Test Product',
            'price': 100,
            'category': category.id,
            'description': 'Test description',
            'stock': 10,  # AGREGADO
            'is_active': True,  # AGREGADO
            'tipo': 'Bebida Caliente'  # OPCIONAL pero incluido
        })
        
        # Debug para ver errores si falla
        if not form.is_valid():
            print("\n=== ERRORES DEL FORMULARIO ===")
            print(form.errors)
        
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_data(self):
        """Test que el form rechaza datos inválidos"""
        form = ProductForm(data={
            'name': '',  # Nombre vacío (INVÁLIDO)
            'price': -10,  # Precio negativo (INVÁLIDO)
        })
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_form_negative_price(self):
        """Test que el form rechaza precios negativos"""
        category = Category.objects.create(name="Test")
        form = ProductForm(data={
            'name': 'Test Product',
            'price': -50,  # INVÁLIDO
            'category': category.id,
            'stock': 10,
            'is_active': True
        })
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)
    
    def test_form_negative_stock(self):
        """Test que el form rechaza stock negativo"""
        category = Category.objects.create(name="Test")
        form = ProductForm(data={
            'name': 'Test Product',
            'price': 100,
            'category': category.id,
            'stock': -5,  # INVÁLIDO
            'is_active': True
        })
        self.assertFalse(form.is_valid())
        self.assertIn('stock', form.errors)