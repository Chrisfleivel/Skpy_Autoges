# contabilidad/permisos.py

"""Permisos iniciales derivados de los decoradores @revisar_permiso en views.py."""

from typing import List, Dict

DEFAULT_SECTOR = 'Contabilidad'


def generar_permisos_iniciales_contabilidad() -> List[Dict[str, str]]:
    """Devuelve los permisos declarados en los views de contabilidad."""
    return [
        {
            'codename': 'contabilidad.marcar_asientos_revisados',
            'nombre': 'Marcar asientos revisados',
            'descripcion': 'Permite marcar asientos contables como revisados.',
            'sector': DEFAULT_SECTOR,
        },
        {
            'codename': 'contabilidad.ver_asientos_contables',
            'nombre': 'Ver asientos contables',
            'descripcion': 'Permite consultar y listar asientos contables.',
            'sector': DEFAULT_SECTOR,
        },
        {
            'codename': 'contabilidad.ver_movimientos_contables',
            'nombre': 'Ver movimientos contables',
            'descripcion': 'Permite ver detalles de movimientos contables.',
            'sector': DEFAULT_SECTOR,
        },
        {
            'codename': 'contabilidad.ver_auditoria_asientos',
            'nombre': 'Ver auditoría de asientos',
            'descripcion': 'Permite acceder a la auditoría de asientos.',
            'sector': DEFAULT_SECTOR,
        },
        {
            'codename': 'contabilidad.ver_reportes',
            'nombre': 'Ver reportes',
            'descripcion': 'Permite consultar reportes contables.',
            'sector': DEFAULT_SECTOR,
        },
    ]


permisos_iniciales_contabilidad = generar_permisos_iniciales_contabilidad()
