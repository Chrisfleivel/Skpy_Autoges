DEFAULT_SECTOR = 'Inventario'


"""Permisos iniciales derivados de los decoradores @revisar_permiso en views.py."""


def generar_permisos_iniciales_inventario():
    """Devuelve los permisos declarados en los views de inventario."""
    return [
    {
        'codename': 'inventario.listar_inventario',
        'nombre': 'Listar Inventario',
        'descripcion': 'Permite agregar un nuevo vehículo al inventario.', 
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_vehiculo',
        'nombre': 'Agregar Vehículo',
        'descripcion': 'Permite agregar un nuevo vehículo al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_vehiculos',
        'nombre': 'Listar Vehículos',
        'descripcion': 'Permite ver la lista de vehículos en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_vehiculo',
        'nombre': 'Detalle Vehículo',
        'descripcion': 'Permite ver los detalles de un vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_vehiculo',
        'nombre': 'Editar Vehículo',
        'descripcion': 'Permite editar un vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_vehiculo',
        'nombre': 'Eliminar Vehículo',
        'descripcion': 'Permite eliminar un vehículo del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_repuesto',
        'nombre': 'Agregar Repuesto',
        'descripcion': 'Permite agregar un nuevo repuesto al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_repuestos',
        'nombre': 'Listar Repuestos',
        'descripcion': 'Permite ver la lista de repuestos en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_repuesto',
        'nombre': 'Detalle Repuesto',
        'descripcion': 'Permite ver los detalles de un repuesto en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_repuesto',
        'nombre': 'Editar Repuesto',
        'descripcion': 'Permite editar un repuesto en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_repuesto',
        'nombre': 'Eliminar Repuesto',
        'descripcion': 'Permite eliminar un repuesto del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_mantenimiento',
        'nombre': 'Agregar Mantenimiento',
        'descripcion': 'Permite agregar un nuevo mantenimiento al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_mantenimientos',
        'nombre': 'Listar Mantenimientos',
        'descripcion': 'Permite ver la lista de mantenimientos en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_mantenimiento',
        'nombre': 'Detalle Mantenimiento',
        'descripcion': 'Permite ver los detalles de un mantenimiento en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_mantenimiento',
        'nombre': 'Editar Mantenimiento',
        'descripcion': 'Permite editar un mantenimiento en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_mantenimiento',
        'nombre': 'Eliminar Mantenimiento',
        'descripcion': 'Permite eliminar un mantenimiento del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.cambiar_estado_mantenimiento',
        'nombre': 'Cambiar Estado del Mantenimiento',
        'descripcion': 'Permite avanzar un mantenimiento de estado (iniciar, finalizar o cancelar).',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_deposito',
        'nombre': 'Agregar Depósito',
        'descripcion': 'Permite agregar un nuevo depósito al inventario.' ,
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_depositos',
        'nombre': 'Listar Depósitos',
        'descripcion': 'Permite ver la lista de depósitos en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_deposito',
        'nombre': 'Detalle Depósito',
        'descripcion': 'Permite ver los detalles de un depósito en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_deposito',
        'nombre': 'Editar Depósito',
        'descripcion': 'Permite editar un depósito en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_deposito',
        'nombre': 'Eliminar Depósito',
        'descripcion': 'Permite eliminar un depósito del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_unidad_medida',
        'nombre': 'Agregar Unidad de Medida',
        'descripcion': 'Permite agregar una nueva unidad de medida al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_unidades_medida',
        'nombre': 'Listar Unidades de Medida',
        'descripcion': 'Permite ver la lista de unidades de medida en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_unidad_medida',
        'nombre': 'Detalle Unidad de Medida',
        'descripcion': 'Permite ver los detalles de una unidad de medida en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_unidad_medida',
        'nombre': 'Editar Unidad de Medida',
        'descripcion': 'Permite editar una unidad de medida en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_unidad_medida',
        'nombre': 'Eliminar Unidad de Medida',
        'descripcion': 'Permite eliminar una unidad de medida del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_marcas_vehiculos',
        'nombre': 'Agregar Marcas de Vehículos',
        'descripcion': 'Permite agregar nuevas marcas de vehículos al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_marcas_vehiculos',
        'nombre': 'Listar Marcas de Vehículos',
        'descripcion': 'Permite ver la lista de marcas de vehículos en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_marcas_vehiculos',
        'nombre': 'Detalle Marca de Vehículo',
        'descripcion': 'Permite ver los detalles de una marca de vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_marcas_vehiculos',
        'nombre': 'Editar Marcas de Vehículos',
        'descripcion': 'Permite editar una marca de vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_marcas_vehiculos',
        'nombre': 'Eliminar Marcas de Vehículos',
        'descripcion': 'Permite eliminar una marca de vehículo del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_tipos_vehiculos',
        'nombre': 'Agregar Tipos de Vehículos',
        'descripcion': 'Permite agregar nuevos tipos de vehículos al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_tipos_vehiculos',
        'nombre': 'Listar Tipos de Vehículos',
        'descripcion': 'Permite ver la lista de tipos de vehículos en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_tipos_vehiculos',
        'nombre': 'Detalle Tipo de Vehículo',
        'descripcion': 'Permite ver los detalles de un tipo de vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_tipos_vehiculos',
        'nombre': 'Editar Tipos de Vehículos',
        'descripcion': 'Permite editar un tipo de vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_tipos_vehiculos',
        'nombre': 'Eliminar Tipos de Vehículos',
        'descripcion': 'Permite eliminar un tipo de vehículo del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_modelos_vehiculos',
        'nombre': 'Agregar Modelos de Vehículos',
        'descripcion': 'Permite agregar nuevos modelos de vehículos al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_modelos_vehiculos',
        'nombre': 'Listar Modelos de Vehículos',
        'descripcion': 'Permite ver la lista de modelos de vehículos en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_modelos_vehiculos',
        'nombre': 'Detalle Modelo de Vehículo',
        'descripcion': 'Permite ver los detalles de un modelo de vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_modelos_vehiculos',
        'nombre': 'Editar Modelos de Vehículos',
        'descripcion': 'Permite editar un modelo de vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_modelos_vehiculos',
        'nombre': 'Eliminar Modelos de Vehículos',
        'descripcion': 'Permite eliminar un modelo de vehículo del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_tipos_transmision',
        'nombre': 'Agregar Tipos de Transmisión',
        'descripcion': 'Permite agregar nuevos tipos de transmisión al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_tipos_transmision',
        'nombre': 'Listar Tipos de Transmisión',
        'descripcion': 'Permite ver la lista de tipos de transmisión en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_tipos_transmision',
        'nombre': 'Detalle Tipo de Transmisión',
        'descripcion': 'Permite ver los detalles de un tipo de transmisión en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_tipos_transmision',
        'nombre': 'Editar Tipos de Transmisión',
        'descripcion': 'Permite editar un tipo de transmisión en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_tipos_transmision',
        'nombre': 'Eliminar Tipos de Transmisión',
        'descripcion': 'Permite eliminar un tipo de transmisión del inventario.',
        'sector': 'Inventario'
    },
]
