

DEFAULT_SECTOR = 'Compras'


"""Permisos iniciales derivados de los decoradores @revisar_permiso en views.py."""


def generar_permisos_iniciales_compras():
    """Devuelve los permisos declarados en los views de compras."""
    return [
        {
            'codename': 'compras.lista_facturas',
            'nombre': 'Listar Facturas Comerciales',
            'descripcion': 'Permite ver la lista de facturas comerciales registradas.',
            'sector': 'Compras',
        },
        {
            'codename': 'compras.agregar_factura',
            'nombre': 'Agregar Factura Comercial',
            'descripcion': 'Permite registrar nuevas facturas comerciales con sus ítems.',
            'sector': 'Compras',
        },
        {
            'codename': 'compras.editar_factura',
            'nombre': 'Editar Factura Comercial',
            'descripcion': 'Permite editar las facturas comerciales en estado borrador.',
            'sector': 'Compras',
        },
        {
            'codename': 'compras.detalle_factura',
            'nombre': 'Detalle de Factura Comercial',
            'descripcion': 'Permite ver el detalle de una factura comercial.',
            'sector': 'Compras',
        },
        {
            'codename': 'compras.eliminar_factura',
            'nombre': 'Eliminar Factura Comercial',
            'descripcion': 'Permite eliminar facturas comerciales en estado borrador.',
            'sector': 'Compras',
        },
        {
            'codename': 'compras.confirmar_factura',
            'nombre': 'Confirmar Factura Comercial',
            'descripcion': 'Permite confirmar una factura comercial para habilitarla al pago.',
            'sector': 'Compras',
        },
    ]
