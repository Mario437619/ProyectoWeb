# miweb/urls.py - Archivo principal de URLs
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin automático de Django
    path('admin/', admin.site.urls),
    
    # Todas las rutas de tu aplicación store (panel, productos, etc.)
    path('', include('store.urls')),
]

# Servir archivos media y static en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)