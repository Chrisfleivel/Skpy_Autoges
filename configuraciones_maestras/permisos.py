

DEFAULT_SECTOR = 'Configuraciones Maestras'


"""Permisos iniciales derivados de los decoradores @revisar_permiso en views.py."""


def generar_permisos_iniciales_configuraciones_maestras():
    """Devuelve los permisos declarados en los views de configuraciones_maestras."""
    return [
        # empresas
        {
            'codename': 'configuraciones_maestras.lista_empresas',
            'nombre': 'Listar Empresas',
            'descripcion': 'Permite ver la lista de Empresas registradas.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.agregar_empresa',
            'nombre': 'Agregar Empresa',
            'descripcion': 'Permite registrar nuevas Empresas.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_empresa',
            'nombre': 'Editar Empresa',
            'descripcion': 'Permite editar los datos de Empresas existentes.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detalles_empresa',
            'nombre': 'Detalles de Empresa',
            'descripcion': 'Permite ver los detalles de una Empresa.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_empresa',
            'nombre': 'Eliminar Empresa',
            'descripcion': 'Permite eliminar Empresas del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        # sucursales
        {
            'codename': 'configuraciones_maestras.lista_sucursales',
            'nombre': 'Listar Sucursales',
            'descripcion': 'Permite ver la lista de Sucursales registradas.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.agregar_sucursal',
            'nombre': 'Agregar Sucursal',
            'descripcion': 'Permite registrar nuevas Sucursales.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_sucursal',
            'nombre': 'Editar Sucursal',
            'descripcion': 'Permite editar los datos de Sucursales existentes.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detalles_sucursal',
            'nombre': 'Detalles de Sucursal',
            'descripcion': 'Permite ver los detalles de una Sucursal.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_sucursal',
            'nombre': 'Eliminar Sucursal',
            'descripcion': 'Permite eliminar Sucursales del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        # cajas (por sucursal)
        {
            'codename': 'configuraciones_maestras.lista_cajas',
            'nombre': 'Listar Cajas',
            'descripcion': 'Permite ver las cajas registradas de una Sucursal.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.agregar_caja',
            'nombre': 'Agregar Caja',
            'descripcion': 'Permite registrar nuevas Cajas en una Sucursal.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_caja',
            'nombre': 'Editar Caja',
            'descripcion': 'Permite editar los datos maestros de Cajas existentes.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detalles_caja',
            'nombre': 'Detalles de Caja',
            'descripcion': 'Permite ver los detalles de una Caja.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_caja',
            'nombre': 'Eliminar Caja',
            'descripcion': 'Permite eliminar Cajas del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        # proveedores
        {
            'codename': 'configuraciones_maestras.agregar_proveedor',
            'nombre': 'Agregar Proveedor',
            'descripcion': 'Permite registrar nuevos Proveedores.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_proveedor',
            'nombre': 'Editar Proveedor',
            'descripcion': 'Permite editar los datos de Proveedores existentes.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_proveedor',
            'nombre': 'Eliminar Proveedor',
            'descripcion': 'Permite eliminar Proveedores del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.inactivar_proveedor',
            'nombre': 'Inactivar Proveedor',
            'descripcion': 'Permite inactivar Proveedores del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.listar_proveedores',
            'nombre': 'Listar Proveedores',
            'descripcion': 'Permite ver la lista de Proveedores registrados.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detallar_proveedor',
            'nombre': 'Detalle de Proveedor',
            'descripcion': 'Permite ver el detalle de un Proveedor.',
            'sector': 'Configuraciones Maestras'
        },
        # agentes de transporte
        {
            'codename': 'configuraciones_maestras.agregar_agente_transporte',
            'nombre': 'Agregar Agente de Transporte',
            'descripcion': 'Permite registrar nuevos Agentes de Transporte.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_agente_transporte',
            'nombre': 'Editar Agente de Transporte',
            'descripcion': 'Permite editar los datos de Agentes de Transporte existentes.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_agente_transporte',
            'nombre': 'Eliminar Agente de Transporte',
            'descripcion': 'Permite eliminar Agentes de Transporte del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.listar_agentes_transporte',
            'nombre': 'Listar Agentes de Transporte',
            'descripcion': 'Permite ver la lista de Agentes de Transporte registrados.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detallar_agente_transporte',
            'nombre': 'Detalle de Agente de Transporte',
            'descripcion': 'Permite ver el detalle de un Agente de Transporte.',
            'sector': 'Configuraciones Maestras'
        },
        # despachantes de aduana
        {
            'codename': 'configuraciones_maestras.agregar_despachante_aduana',
            'nombre': 'Agregar Despachante de Aduana',
            'descripcion': 'Permite registrar nuevos Despachantes de Aduana.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_despachante_aduana',
            'nombre': 'Editar Despachante de Aduana',
            'descripcion': 'Permite editar los datos de Despachantes de Aduana existentes.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_despachante_aduana',
            'nombre': 'Eliminar Despachante de Aduana',
            'descripcion': 'Permite eliminar Despachantes de Aduana del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.listar_despachantes_aduana',
            'nombre': 'Listar Despachantes de Aduana',
            'descripcion': 'Permite ver la lista de Despachantes de Aduana registrados.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detallar_despachante_aduana',
            'nombre': 'Detalle de Despachante de Aduana',
            'descripcion': 'Permite ver el detalle de un Despachante de Aduana.',
            'sector': 'Configuraciones Maestras'
        },
        # tasas de cambio
        {
            'codename': 'configuraciones_maestras.agregar_tasa_cambio',
            'nombre': 'Agregar Tasa de Cambio',
            'descripcion': 'Permite registrar nuevas Tasas de Cambio.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_tasa_cambio',
            'nombre': 'Editar Tasa de Cambio',
            'descripcion': 'Permite editar los datos de Tasas de Cambio existentes.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_tasa_cambio',
            'nombre': 'Eliminar Tasa de Cambio',
            'descripcion': 'Permite eliminar Tasas de Cambio del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.listar_tasas_cambio',
            'nombre': 'Listar Tasas de Cambio',
            'descripcion': 'Permite ver la lista de Tasas de Cambio registradas.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detallar_tasa_cambio',
            'nombre': 'Detalle de Tasa de Cambio',
            'descripcion': 'Permite ver el detalle de una Tasa de Cambio.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.agregar_departamento',
            'nombre': 'Agregar Departamento',
            'descripcion': 'Permite registrar nuevos Departamentos.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_departamento',
            'nombre': 'Editar Departamento',
            'descripcion': 'Permite editar los datos de Departamentos existentes.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_departamento',
            'nombre': 'Eliminar Departamento',
            'descripcion': 'Permite eliminar Departamentos del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.inactivar_departamento',
            'nombre': 'Inactivar Departamento',
            'descripcion': 'Permite inactivar Departamentos del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.activar_departamento',
            'nombre': 'Activar Departamento',
            'descripcion': 'Permite activar Departamentos del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.listar_departamentos',
            'nombre': 'Listar Departamentos',
            'descripcion': 'Permite ver la lista de Departamentos registrados.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detallar_departamento',
            'nombre': 'Detalle de Departamento',
            'descripcion': 'Permite ver el detalle de un Departamento.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.agregar_cargo',
            'nombre': 'Agregar Cargo',
            'descripcion': 'Permite registrar nuevos Cargos.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_cargo',
            'nombre': 'Editar Cargo',
            'descripcion': 'Permite editar los datos de Cargos existentes.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_cargo',
            'nombre': 'Eliminar Cargo',
            'descripcion': 'Permite eliminar Cargos del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.inactivar_cargo',
            'nombre': 'Inactivar Cargo',
            'descripcion': 'Permite inactivar Cargos del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.activar_cargo',
            'nombre': 'Activar Cargo',
            'descripcion': 'Permite activar Cargos del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.listar_cargos',
            'nombre': 'Listar Cargos',
            'descripcion': 'Permite ver la lista de Cargos registrados.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detallar_cargo',
            'nombre': 'Detalle de Cargo',
            'descripcion': 'Permite ver el detalle de un Cargo.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.registrar_compra',
            'nombre': 'Registrar Compra',
            'descripcion': 'Permite registrar nuevas compras en el sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.agregar_despachante',
            'nombre': 'Agregar Despachante',
            'descripcion': 'Permite registrar nuevos despachantes en el sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_despachante',
            'nombre': 'Editar Despachante',
            'descripcion': 'Permite editar los datos de despachantes existentes.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_despachante',
            'nombre': 'Eliminar Despachante',
            'descripcion': 'Permite eliminar despachantes del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detallar_despachante',
            'nombre': 'Detalle de Despachante',
            'descripcion': 'Permite ver el detalle de un Despachante.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.listar_despachantes',
            'nombre': 'Listar Despachantes',
            'descripcion': 'Permite ver la lista de Despachantes registrados.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.listar_monedas',
            'nombre': 'Listar Monedas',
            'descripcion': 'Permite ver la lista de Monedas registradas.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.agregar_moneda',
            'nombre': 'Agregar Moneda',
            'descripcion': 'Permite registrar nuevas monedas en el sistema.',
            'sector': 'Configuraciones Maestras'
        }
        ,
        {
            'codename': 'configuraciones_maestras.eliminar_moneda',
            'nombre': 'Eliminar Moneda',
            'descripcion': 'Permite eliminar monedas del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_moneda',
            'nombre': 'Editar Moneda',
            'descripcion': 'Permite editar los datos de monedas existentes.',
            'sector': 'Configuraciones Maestras'
        }
        ,
        {
            'codename': 'configuraciones_maestras.detallar_moneda',
            'nombre': 'Detalle de Moneda',
            'descripcion': 'Permite ver el detalle de una Moneda.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.lista_bancos',
            'nombre': 'Listar Bancos',
            'descripcion': 'Permite ver la lista de bancos habilitados para pagos exteriores.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.agregar_banco',
            'nombre': 'Agregar Banco',
            'descripcion': 'Permite registrar bancos para pagos exteriores.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.lista_ordenes_pago_exterior',
            'nombre': 'Listar Órdenes de Pago Exterior',
            'descripcion': 'Permite ver la lista de órdenes de pago exterior.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.agregar_orden_pago_exterior',
            'nombre': 'Agregar Orden de Pago Exterior',
            'descripcion': 'Permite crear nuevas órdenes de pago exterior.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_orden_pago_exterior',
            'nombre': 'Editar Orden de Pago Exterior',
            'descripcion': 'Permite modificar órdenes de pago exterior.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detalle_orden_pago_exterior',
            'nombre': 'Detalle de Orden de Pago Exterior',
            'descripcion': 'Permite consultar el detalle completo de una orden de pago exterior.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_orden_pago_exterior',
            'nombre': 'Eliminar Orden de Pago Exterior',
            'descripcion': 'Permite eliminar órdenes de pago exterior del sistema.',
            'sector': 'Configuraciones Maestras'
        }

    ]
