import os
import sys
import django
import traceback
from datetime import date
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skpy_autogest_project.settings')
# Ensure project root is on sys.path so Django settings can be imported
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
django.setup()

from configuraciones_maestras.models import Proveedor
from inventario.models import Repuesto
from clientes_pedidos.models import FacturaCompraProveedor, FacturaCompraItem, Pedido

def main():
    try:
        print('INICIANDO SCRIPT DE PRUEBA')
        # Obtener o crear proveedor
        proveedor = Proveedor.objects.first()
        if not proveedor:
            proveedor = Proveedor.objects.create(nombre='Proveedor Prueba', tipo_persona='JURIDICA')

        # Obtener o crear repuestos
        repuestos = list(Repuesto.objects.filter(proveedor=proveedor)[:2])
        if len(repuestos) < 2:
            for i in range(2 - len(repuestos)):
                r = Repuesto.objects.create(
                    nombre=f'Repuesto prueba {i+1}',
                    proveedor=proveedor,
                    tipo='repuesto',
                    estado='disponible',
                    costo_compra=Decimal('100.00')
                )
                repuestos.append(r)

        # Obtener pedidos de abastecimiento existentes
        pedidos = list(Pedido.objects.filter(tipo='abastecimiento')[:2])
        if not pedidos:
            cliente = None
            if Pedido.objects.exists():
                cliente = Pedido.objects.first().cliente
            pedidos.append(Pedido.objects.create(cliente=cliente or None, tipo='abastecimiento'))

        # Crear factura
        factura = FacturaCompraProveedor.objects.create(
            proveedor=proveedor,
            numero_factura='TEST-001',
            fecha_factura=date.today()
        )

        # Agregar items
        for r in repuestos:
            FacturaCompraItem.objects.create(
                factura=factura,
                repuesto=r,
                cantidad=2,
                precio_unitario=(r.costo_compra or Decimal('100.00'))
            )

        factura.calcular_totales()

        # Asociar pedidos
        for p in pedidos:
            factura.pedidos.add(p)
            p.proveedor_compra = proveedor
            p.numero_factura = factura.numero_factura
            p.fecha_factura = factura.fecha_factura
            p.factura_pdf = None
            p.monto_total = p.calcular_monto_total()
            p.iva = p.calcular_iva()
            p.save()

        print('Factura creada id=', factura.id, 'monto_total=', factura.monto_total, 'iva=', factura.iva)
        print('Items:', factura.items.count())
        print('Pedidos asociados:', factura.pedidos.count())
    except Exception:
        print('ERROR al ejecutar script:')
        traceback.print_exc()

if __name__ == '__main__':
    main()
