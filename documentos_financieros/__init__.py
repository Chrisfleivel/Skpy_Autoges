# documentos_financieros/__init__.py

from django.apps import AppConfig

# Se define una clase de configuración para la aplicación
class DocumentosFinancierosConfig(AppConfig):
    # Nombre de la aplicación (nombre de la carpeta)
    name = 'documentos_financieros'
    # Nombre descriptivo que aparecerá en el panel de administración, etc.
    verbose_name = "Documentos Financieros"

# Se importa la clase de configuración para que esté disponible
default_app_config = 'documentos_financieros.DocumentosFinancierosConfig'

# En un comentario, se puede agregar una descripción más detallada
"""
Esta aplicación gestiona la creación y el ciclo de vida de los documentos financieros
del sistema SKPY AutoGest, asegurando el cumplimiento con las normativas fiscales
(Manual Técnico SIFEN).
Sus funcionalidades clave incluyen:
- Generación de documentos electrónicos (DE) como Facturas (Crédito y Contado),
  Notas de Crédito, Notas de Débito, Autofacturas y Notas de Remisión.
- Estructuración de los datos según las especificaciones técnicas del SIFEN.
- Lógica para la generación de la representación gráfica de estos documentos en formato PDF.
Esta aplicación interactúa con los módulos de ventas y cobranzas para generar
los documentos y con el módulo de reportes para su consulta.
"""