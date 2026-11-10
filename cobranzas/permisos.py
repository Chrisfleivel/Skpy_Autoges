
"""Permisos iniciales derivados de los decoradores @revisar_permiso en views.py."""


def generar_permisos_iniciales_cobranzas():
    """Devuelve los permisos declarados en los views de cobranzas."""
    return [ 
    {
        'codename': 'cobranzas.lista_pedidos_cobranzas',
        'nombre': 'Listar Pedidos en Cobranzas',
        'descripcion': 'Permite ver la lista de todos los pedidos en cobranzas.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.panel_caja',
        'nombre': 'Panel de Caja',
        'descripcion': 'Permite acceder al panel principal de cajas, aperturas y cierres.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.abrir_caja',
        'nombre': 'Abrir Caja',
        'descripcion': 'Permite abrir una caja y registrar el saldo inicial.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.cerrar_caja',
        'nombre': 'Cerrar Caja',
        'descripcion': 'Permite cerrar caja y registrar el arqueo final.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.lista_pedidos_busqueda',
        'nombre': 'Buscar Pedidos en Cobranzas',
        'descripcion': 'Permite buscar pedidos en cobranzas.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.lista_pedidos_transferencia',
        'nombre': 'Listar Pedidos en Transferencia',
        'descripcion': 'Permite ver la lista de todos los pedidos en transferencia.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.lista_pedidos_despacho',
        'nombre': 'Listar Pedidos en Despacho',
        'descripcion': 'Permite ver la lista de todos los pedidos en despacho.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.cancelar_pedido_cobranzas',
        'nombre': 'Cancelar Pedido en Cobranzas',
        'descripcion': 'Permite cancelar pedidos en cobranzas.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.facturar_contado_cobranzas',
        'nombre': 'Facturar Contado en Cobranzas',
        'descripcion': 'Permite facturar pedidos al contado en cobranzas.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.descargar_factura_cobranzas',
        'nombre': 'Descargar Factura en Cobranzas',
        'descripcion': 'Permite descargar la factura de pedidos en cobranzas.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.cobrar_pedido',
        'nombre': 'Cobrar Pedido',
        'descripcion': 'Permite registrar el cobro de un pedido en cobranzas.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.agregar_venta',
        'nombre': 'Agregar Venta',
        'descripcion': 'Permite registrar nuevas ventas en cobranzas.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.previsualizar_factura_cobranzas',
        'nombre': 'Previsualizar Factura en Cobranzas',
        'descripcion': 'Permite previsualizar la factura de pedidos en cobranzas.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.entregar_repuesto_cobranzas',
        'nombre': 'Entregar Repuesto en Cobranzas',
        'descripcion': 'Permite registrar la entrega de repuestos en cobranzas.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.iniciar_transferencia_cobranzas',
        'nombre': 'Iniciar Transferencia en Cobranzas',
        'descripcion': 'Permite iniciar el proceso de transferencia de pedidos en cobranzas.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.confirmar_transferencia_cobranzas',
        'nombre': 'Confirmar Transferencia en Cobranzas',
        'descripcion': 'Permite confirmar el proceso de transferencia de pedidos en cobranzas.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.confirmar_pago_cobranzas',
        'nombre': 'Confirmar Pago en Cobranzas',
        'descripcion': 'Permite confirmar el pago de pedidos en cobranzas.',
        'sector': 'Cobranzas'
    },
    {
        'codename': 'cobranzas.facturar_pedido_cobranzas',
        'nombre': 'Facturar Pedido en Cobranzas',
        'descripcion': 'Permite facturar pedidos en cobranzas.',
        'sector': 'Cobranzas'
    }

]
