# miweb/urls.py - Archivo principal de URLs

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Admin automático de Django (mantener)
    path('admin/', admin.site.urls),
    
    # Todas las rutas de tu aplicación store (panel, productos, etc.)
    path('', include('store.urls')),
]