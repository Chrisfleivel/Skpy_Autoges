
DEFAULT_SECTOR = 'Importaciones'


"""Permisos iniciales derivados de los decoradores @revisar_permiso en views.py."""


def generar_permisos_iniciales_importaciones():
    """Devuelve los permisos declarados en los views de importaciones."""
    return [
        
        {
            'codename': 'importaciones.listar_documentos',
            'nombre': 'Listar Documentos',
            'descripcion': 'Permite ver la lista de Documentos registrados.',
            'sector': 'Importaciones',
        },
        {
            'codename': 'importaciones.agregar_documento',
            'nombre': 'Agregar Documento',
            'descripcion': 'Permite agregar un nuevo Documento a una Importación.',
            'sector': 'Importaciones',
        },
        {
            'codename': 'importaciones.editar_importacion_aduana',
            'nombre': 'Editar Importación Aduana',
            'descripcion': 'Permite editar los datos de la Importación relacionados con Aduana.',
            'sector': 'Importaciones',
        },
        {
            'codename': 'importaciones.listar_importaciones',
            'nombre': 'Listar Importaciones',
            'descripcion': 'Permite ver la lista de Importaciones registradas.',
            'sector': 'Importaciones',
        },
        {
            'codename': 'importaciones.agregar_importacion',
            'nombre': 'Agregar Importación',
            'descripcion': 'Permite agregar una nueva Importación.',
            'sector': 'Importaciones',
        },
        {
            'codename': 'importaciones.editar_importacion',
            'nombre': 'Editar Importación',
            'descripcion': 'Permite editar los datos de una Importación existente.',
            'sector': 'Importaciones',
        },
        {
            'codename': 'importaciones.detallar_importacion',
            'nombre': 'Detallar Importación',
            'descripcion': 'Permite ver el detalle completo de una Importación.',
            'sector': 'Importaciones',
        },
        {
            'codename': 'importaciones.eliminar_importacion',
            'nombre': 'Eliminar Importación',
            'descripcion': 'Permite eliminar una Importación existente.',
            'sector': 'Importaciones',
        }
]