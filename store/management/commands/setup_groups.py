# store/management/commands/setup_groups.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from store.models import Product, Category, Order

class Command(BaseCommand):
    help = 'Crea los grupos Administrador y Vendedor con sus permisos'

    def handle(self, *args, **kwargs):
        # Crear grupo Administrador
        admin_group, created = Group.objects.get_or_create(name='Administrador')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Administrador" creado'))
        else:
            self.stdout.write(self.style.WARNING('○ Grupo "Administrador" ya existe'))
        
        # Asignar TODOS los permisos al administrador
        admin_group.permissions.set(Permission.objects.all())
        
        # Crear grupo Vendedor
        vendedor_group, created = Group.objects.get_or_create(name='Vendedor')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Vendedor" creado'))
        else:
            self.stdout.write(self.style.WARNING('○ Grupo "Vendedor" ya existe'))
        
        # Permisos limitados para vendedor (solo ver productos y crear órdenes)
        vendedor_perms = []
        
        # Puede ver productos
        product_ct = ContentType.objects.get_for_model(Product)
        vendedor_perms.append(Permission.objects.get(codename='view_product', content_type=product_ct))
        
        # Puede crear y ver órdenes
        order_ct = ContentType.objects.get_for_model(Order)
        vendedor_perms.extend([
            Permission.objects.get(codename='add_order', content_type=order_ct),
            Permission.objects.get(codename='view_order', content_type=order_ct),
        ])
        
        vendedor_group.permissions.set(vendedor_perms)
        
        self.stdout.write(self.style.SUCCESS('\n✓ Grupos configurados correctamente'))
        self.stdout.write(self.style.SUCCESS('  - Administrador: Acceso completo'))
        self.stdout.write(self.style.SUCCESS('  - Vendedor: Solo ventas\n'))