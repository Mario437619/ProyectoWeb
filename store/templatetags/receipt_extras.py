# store/templatetags/receipt_extras.py
# Crear esta carpeta y archivo: store/templatetags/receipt_extras.py

from django import template
import re

register = template.Library()

@register.filter
def extract_payment(notes):
    """Extrae el monto del pago del campo notes"""
    if not notes:
        return "0.00"
    
    # Buscar patrón: Pago: $100.00
    match = re.search(r'Pago:\s*\$(\d+\.?\d*)', notes)
    if match:
        return match.group(1)
    return "0.00"

@register.filter
def extract_change(notes):
    """Extrae el cambio del campo notes"""
    if not notes:
        return "0.00"
    
    # Buscar patrón: Cambio: $5.00
    match = re.search(r'Cambio:\s*\$(\d+\.?\d*)', notes)
    if match:
        return match.group(1)
    return "0.00"