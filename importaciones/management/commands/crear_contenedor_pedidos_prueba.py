from django.core.management.base import BaseCommand

from configuraciones_maestras.models import Proveedor
from importaciones.models import ContenedorImportacion, PedidoProveedorImportacion


class Command(BaseCommand):
    help = 'Crea un contenedor de importación y registra pedidos de prueba para los proveedores disponibles.'

    def handle(self, *args, **options):
        contenedor, created = ContenedorImportacion.objects.get_or_create(
            numero='CNT-PRUEBA-001',
            defaults={
                'descripcion': 'Contenedor de prueba para pedidos de proveedores',
                'estado': 'pendiente',
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Contenedor creado: {contenedor.numero}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ El contenedor ya existe: {contenedor.numero}'))

        proveedores = Proveedor.objects.all()
        if not proveedores.exists():
            proveedor_a = Proveedor.objects.create(nombre='Proveedor Prueba A', razon_social='Proveedor Prueba A', ruc='8001111110001')
            proveedor_b = Proveedor.objects.create(nombre='Proveedor Prueba B', razon_social='Proveedor Prueba B', ruc='8002222220002')
            proveedores = Proveedor.objects.filter(id__in=[proveedor_a.id, proveedor_b.id])

        creados = 0
        for proveedor in proveedores:
            pedido, pedido_created = PedidoProveedorImportacion.objects.get_or_create(
                codigo=f'PO-{proveedor.id}',
                defaults={
                    'contenedor': contenedor,
                    'proveedor': proveedor,
                    'estado': 'pendiente',
                    'observaciones': 'Pedido creado por comando de prueba',
                },
            )
            if pedido_created:
                creados += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Pedido creado para {proveedor}: {pedido.codigo}'))
            else:
                self.stdout.write(self.style.WARNING(f'ℹ Pedido ya existe para {proveedor}: {pedido.codigo}'))

        self.stdout.write(self.style.SUCCESS(f'Pedidos creados/confirmados: {creados}'))
        self.stdout.write(self.style.SUCCESS('Resumen del contenedor:'))
        for pedido in contenedor.pedidos_proveedor.all():
            self.stdout.write(f'  • {pedido.codigo} -> {pedido.proveedor}')
