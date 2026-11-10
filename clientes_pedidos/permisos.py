"""Permisos iniciales derivados de los decoradores @revisar_permiso en views.py."""


def generar_permisos_iniciales_clientes_pedidos():
    """Devuelve los permisos declarados en los views de clientes_pedidos."""
    return [ 
        {
            'codename': 'clientes_pedidos.agregar_cliente',
            'nombre': 'Agregar Cliente',
            'descripcion': 'Permite registrar nuevos Clientes.',
            'sector': 'Clientes y Pedidos'
        }, 
        {
            'codename': 'clientes_pedidos.editar_cliente',
            'nombre': 'Editar Cliente',
            'descripcion': 'Permite modificar la información de Clientes existentes.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.listar_clientes',
            'nombre': 'Listar Clientes',
            'descripcion': 'Permite ver la lista de todos los Clientes.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.detallar_cliente',
            'nombre': 'Detalle de Cliente',
            'descripcion': 'Permite ver los detalles de un Cliente específico.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.agregar_pedido',
            'nombre': 'Agregar Pedido',
            'descripcion': 'Permite registrar nuevos Pedidos.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido',
            'nombre': 'Editar Pedido',
            'descripcion': 'Permite modificar la información de Pedidos existentes.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.listar_pedidos',
            'nombre': 'Listar Pedidos',
            'descripcion': 'Permite ver la lista de todos los Pedidos.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.detallar_pedido',
            'nombre': 'Detalle de Pedido',
            'descripcion': 'Permite ver los detalles de un Pedido específico.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.agregar_item_pedido',
            'nombre': 'Agregar Item de Pedido',
            'descripcion': 'Permite agregar nuevos Items a un Pedido.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_item_pedido',
            'nombre': 'Editar Item de Pedido',
            'descripcion': 'Permite modificar la información de Items de Pedidos existentes.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.listar_items_pedido',
            'nombre': 'Listar Items de Pedido',
            'descripcion': 'Permite ver la lista de todos los Items de un Pedido.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.detallar_item_pedido',
            'nombre': 'Detalle de Item de Pedido',
            'descripcion': 'Permite ver los detalles de un Item específico de un Pedido.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.agregar_cotizacion',
            'nombre': 'Agregar Cotización',
            'descripcion': 'Permite registrar nuevas Cotizaciones.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_cotizacion',
            'nombre': 'Editar Cotización',
            'descripcion': 'Permite modificar la información de Cotizaciones existentes.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.listar_cotizaciones',
            'nombre': 'Listar Cotizaciones',
            'descripcion': 'Permite ver la lista de todas las Cotizaciones.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.detallar_cotizacion',
            'nombre': 'Detalle de Cotización',
            'descripcion': 'Permite ver los detalles de una Cotización específica.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.realizar_pedido',
            'nombre': 'Realizar Pedido',
            'descripcion': 'Permite a los empleados realizar pedidos para los clientes.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.realizar_pedido_a_medida',
            'nombre': 'Realizar Pedido a Medida',
            'descripcion': 'Permite a los empleados realizar pedidos de importación a medida para los clientes.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.realizar_pedido_abastecimiento',
            'nombre': 'Realizar Pedido de Abastecimiento',
            'descripcion': 'Permite a los empleados realizar pedidos de abastecimiento para los clientes.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.realizar_pedido_busqueda',
            'nombre': 'Realizar Pedido de Búsqueda',
            'descripcion': 'Permite a los empleados realizar pedidos de búsqueda para los clientes.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.exportar_pedido_pdf',
            'nombre': 'Exportar Pedido a PDF',
            'descripcion': 'Permite exportar los detalles de un pedido a un archivo PDF.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.cargar_factura_pedido',
            'nombre': 'Cargar Factura de Pedido',
            'descripcion': 'Permite cargar la factura correspondiente a un pedido.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.detalle_carrito',
            'nombre': 'Detalle de Carrito',
            'descripcion': 'Permite ver los detalles del carrito de compras del cliente.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.agregar_al_carrito',
            'nombre': 'Agregar al Carrito',
            'descripcion': 'Permite agregar productos al carrito de compras del cliente.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.enviar_a_seleccion',
            'nombre': 'Enviar Pedido a Selección',
            'descripcion': 'Permite enviar un pedido de búsqueda o abastecimiento al encargado de selección de producto.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.listar_pedidos_seleccion',
            'nombre': 'Listar Pedidos para Selección',
            'descripcion': 'Permite listar pedidos de búsqueda y abastecimiento pendientes de selección para el encargado.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.confirmar_producto_buscado',
            'nombre': 'Confirmar Producto Buscado',
            'descripcion': 'Permite al encargado confirmar el producto encontrado y establecer el precio.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.detallar_pedido.imprimir_producto_buscado',
            'nombre': 'Imprimir Producto Buscado',
            'descripcion': 'Permite imprimir los detalles del producto buscado en un pedido.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.enviar_precio_cliente',
            'nombre': 'Enviar Precio al Cliente',
            'descripcion': 'Permite enviar el precio confirmado al cliente para su aprobación.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.detallar_pedido.confirmar_precio_cliente',
            'nombre': 'Confirmar Precio por Cliente',
            'descripcion': 'Permite al cliente confirmar el precio y convertir el pedido en un pedido de importación.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.aprobar',
            'nombre': 'Aprobar Pedido',
            'descripcion': 'Permite aprobar un pedido pendiente.',
            'sector': 'Clientes y Pedidos'
        }, 
        {
            'codename': 'clientes_pedidos.editar_pedido.rechazar',
            'nombre': 'Rechazar Pedido',
            'descripcion': 'Permite rechazar un pedido pendiente.',
            'sector': 'Clientes y Pedidos'
        }, 
        {
            'codename': 'clientes_pedidos.editar_pedido.aprobar_rechazar_abastecimiento',
            'nombre': 'Aprobar/Rechazar Pedido de Abastecimiento',
            'descripcion': 'Permite aprobar o rechazar un pedido de abastecimiento.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.actualizar_item',
            'nombre': 'Actualizar Item de Pedido',
            'descripcion': 'Permite actualizar la información de un item en el pedido.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.enviar_a_cobranzas',
            'nombre': 'Enviar a Cobranzas',
            'descripcion': 'Permite enviar un pedido a la sección de cobranzas.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.facturar_pedido_contado',
            'nombre': 'Facturar Pedido Contado',
            'descripcion': 'Permite facturar un pedido realizado en efectivo.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.confirmar_entrega_repuesto',
            'nombre': 'Confirmar Entrega de Repuesto',
            'descripcion': 'Permite confirmar la entrega de un repuesto en un pedido.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.programar_transferencia',
            'nombre': 'Programar Transferencia',
            'descripcion': 'Permite programar la transferencia de un pedido.',
            'sector': 'Clientes y Pedidos'
        }, 
        {
            'codename': 'clientes_pedidos.editar_pedido.iniciar_transferencia',
            'nombre': 'Iniciar Transferencia',
            'descripcion': 'Permite iniciar la transferencia de un pedido.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.confirmar_transferencia',
            'nombre': 'Confirmar Transferencia',
            'descripcion': 'Permite confirmar la transferencia de un pedido.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.cancelar',
            'nombre': 'Cancelar Pedido',
            'descripcion': 'Permite cancelar un pedido.',
            'sector': 'Clientes y Pedidos'
        }, 
        {
            'codename': 'clientes_pedidos.editar_pedido.avanzar_busqueda',
            'nombre': 'Avanzar Búsqueda',
            'descripcion': 'Permite avanzar en la búsqueda de un producto.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.cargar_factura',
            'nombre': 'Cargar Factura',
            'descripcion': 'Permite cargar la factura de un pedido.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.eliminar_cliente',
            'nombre': 'Eliminar Cliente',
            'descripcion': 'Permite eliminar un cliente del sistema.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.obtener_precio_repuesto',
            'nombre': 'Obtener Precio de Repuesto',
            'descripcion': 'Permite obtener el precio de un repuesto.',
            'sector': 'Clientes y Pedidos'
        },
        {
            'codename': 'clientes_pedidos.obtener_precio_vehiculo',
            'nombre': 'Obtener Precio de Vehículo',
            'descripcion': 'Permite obtener el precio de un vehículo.',
            'sector': 'Clientes y Pedidos'
        }
    ]