# configuraciones_maestras/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import inlineformset_factory
from django.utils import timezone
from decimal import Decimal

from core.models import Moneda as MonedaFacade, TasaCambio as TasaCambioFacade
from .models import Proveedor, ContactoProveedor, AgenteTransporte, DespachanteAduana, Despachante, TasaCambio, Departamento, Cargo, Moneda, Empresa, Banco, OrdenPagoExterior, Sucursal
from .forms import (
    EmpresaForm,
    SucursalForm,
    CajaForm,
    AperturaCajaOperativaForm,
    CierreCajaOperativaForm,
    ProveedorForm,
    ContactoProveedorForm,
    AgenteTransporteForm,
    DespachanteAduanaForm,
    DespachanteForm,
    TasaCambioForm,
    DepartamentoForm,
    CargoForm,
    MonedaForm,
    BancoForm,
    OrdenPagoExteriorForm,
    RegistroPagoDesdeOrdenForm,
)
from .services import registrar_pago_desde_orden
from seguridad_usuarios.decorators import revisar_permiso
from cobranzas.models import Caja as CajaOperativa, AperturaCaja as AperturaCajaOperativa, CierreCaja as CierreCajaOperativa
# login_required
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.shortcuts import HttpResponse

# Importar modelos necesarios para registrar la compra
from inventario.models import Repuesto
from clientes_pedidos.models import Pedido, Cliente as ClientePedido, FacturaCompraProveedor

ContactoProveedorFormSet = inlineformset_factory(
    Proveedor,
    ContactoProveedor,
    form=ContactoProveedorForm,
    extra=1,
    can_delete=True,
)

# Vista principal de datos maestros
def home_maestras(request):
    return render(request, 'configuraciones_maestras/home_maestras.html')


@revisar_permiso('configuraciones_maestras.lista_ordenes_pago_exterior')
def lista_ordenes_pago_exterior(request):
    ordenes = OrdenPagoExterior.objects.select_related(
        'moneda', 'banco_corresponsal', 'banco_beneficiario', 'factura', 'embarque',
    ).all().order_by('-fecha_operacion', '-created_at')
    return render(request, 'configuraciones_maestras/lista_ordenes_pago_exterior.html', {'ordenes': ordenes})


@revisar_permiso('configuraciones_maestras.agregar_orden_pago_exterior')
def agregar_orden_pago_exterior(request):
    if request.method == 'POST':
        form = OrdenPagoExteriorForm(request.POST, request.FILES)
        if form.is_valid():
            orden = form.save(commit=False)
            orden.usuario_creo = request.user if request.user.is_authenticated else None
            orden.save()
            messages.success(request, 'Orden de pago exterior registrada correctamente.')
            return redirect('lista_ordenes_pago_exterior')
    else:
        form = OrdenPagoExteriorForm(initial={'fecha_operacion': timezone.now().date(), 'estado': 'BORRADOR'})
    return render(request, 'configuraciones_maestras/agregar_orden_pago_exterior.html', {'form': form})


@revisar_permiso('configuraciones_maestras.editar_orden_pago_exterior')
def editar_orden_pago_exterior(request, pk):
    orden = get_object_or_404(OrdenPagoExterior, pk=pk)
    if request.method == 'POST':
        form = OrdenPagoExteriorForm(request.POST, request.FILES, instance=orden)
        if form.is_valid():
            orden = form.save(commit=False)
            orden.save()
            messages.success(request, 'Orden actualizada correctamente.')
            return redirect('detalle_orden_pago_exterior', pk=orden.pk)
    else:
        form = OrdenPagoExteriorForm(instance=orden)
    return render(request, 'configuraciones_maestras/editar_orden_pago_exterior.html', {'form': form, 'orden': orden})


@revisar_permiso('configuraciones_maestras.detalle_orden_pago_exterior')
def detalle_orden_pago_exterior(request, pk):
    orden = get_object_or_404(
        OrdenPagoExterior.objects.select_related(
            'moneda', 'banco_corresponsal', 'banco_beneficiario', 'factura__proveedor',
            'embarque', 'pago_exterior',
        ),
        pk=pk,
    )
    return render(request, 'configuraciones_maestras/detalle_orden_pago_exterior.html', {'orden': orden})


@revisar_permiso('configuraciones_maestras.eliminar_orden_pago_exterior')
def eliminar_orden_pago_exterior(request, pk):
    orden = get_object_or_404(OrdenPagoExterior, pk=pk)
    if orden.pago_registrado:
        messages.error(request, 'La liquidación tiene un pago registrado: no se puede eliminar.')
        return redirect('detalle_orden_pago_exterior', pk=orden.pk)
    if request.method == 'POST':
        orden.delete()
        messages.success(request, 'Orden eliminada correctamente.')
        return redirect('lista_ordenes_pago_exterior')
    return render(request, 'configuraciones_maestras/eliminar_orden_pago_exterior.html', {'orden': orden})


@revisar_permiso('configuraciones_maestras.registrar_pago_orden_exterior')
def registrar_pago_desde_liquidacion(request, pk):
    """
    Registra el pago al exterior a partir de la liquidación.

    La liquidación aporta los datos bancarios y los importes; el usuario
    confirma a qué factura se imputa y en qué embarque se carga la comisión.
    """
    orden = get_object_or_404(
        OrdenPagoExterior.objects.select_related('moneda', 'factura', 'embarque'),
        pk=pk,
    )

    if orden.pago_registrado:
        messages.info(request, 'Esta liquidación ya tiene un pago registrado.')
        return redirect('detalle_orden_pago_exterior', pk=orden.pk)

    if request.method == 'POST':
        form = RegistroPagoDesdeOrdenForm(request.POST, orden=orden)
        if form.is_valid():
            try:
                pago = registrar_pago_desde_orden(
                    orden,
                    factura=form.cleaned_data['factura'],
                    fecha_operacion=form.cleaned_data['fecha_operacion'],
                    importe=form.cleaned_data['importe'],
                    comision=form.cleaned_data.get('comision') or Decimal('0'),
                    cotizacion=form.cleaned_data.get('cotizacion'),
                    embarque=form.cleaned_data.get('embarque'),
                    forma_pago=form.cleaned_data.get('forma_pago'),
                    referencia_op=form.cleaned_data.get('referencia_op') or '',
                    numero_lote=form.cleaned_data.get('numero_lote') or '',
                    usuario=request.user if request.user.is_authenticated else None,
                )
            except ValidationError as exc:
                messages.error(request, '; '.join(exc.messages))
            else:
                messages.success(
                    request,
                    f'Pago {pago.referencia_op or pago.pk} registrado. '
                    f'La factura {pago.factura.numero} quedó con saldo pendiente {pago.factura.saldo_pendiente}.',
                )
                return redirect('detalle_orden_pago_exterior', pk=orden.pk)
    else:
        form = RegistroPagoDesdeOrdenForm(orden=orden)

    return render(
        request,
        'configuraciones_maestras/registrar_pago_orden_pago_exterior.html',
        {'form': form, 'orden': orden},
    )


@revisar_permiso('configuraciones_maestras.lista_bancos')
def lista_bancos(request):
    bancos = Banco.objects.all().order_by('nombre')
    return render(request, 'configuraciones_maestras/lista_bancos.html', {'bancos': bancos})


@revisar_permiso('configuraciones_maestras.agregar_banco')
def agregar_banco(request):
    if request.method == 'POST':
        form = BancoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Banco registrado correctamente.')
            return redirect('lista_bancos')
    else:
        form = BancoForm()
    return render(request, 'configuraciones_maestras/agregar_banco.html', {'form': form})


# CRUD Empresa
@revisar_permiso('configuraciones_maestras.lista_empresas')
def lista_empresas(request):
    empresa = Empresa.get_empresa_activa()
    return render(request, 'configuraciones_maestras/lista_empresas.html', {'empresa': empresa})


@revisar_permiso('configuraciones_maestras.agregar_empresa')
def agregar_empresa(request):
    if Empresa.objects.exists():
        messages.warning(request, 'El sistema solo admite una empresa activa. Se trabaja sobre la empresa registrada.')
        return redirect('lista_empresas')

    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.usuario_modifico = request.user if request.user.is_authenticated else None
            empresa.save()
            form.save_m2m()
            messages.success(request, 'Empresa registrada correctamente.')
            return redirect('lista_empresas')
    else:
        form = EmpresaForm()
    return render(request, 'configuraciones_maestras/agregar_empresa.html', {'form': form})


@revisar_permiso('configuraciones_maestras.editar_empresa')
def editar_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.usuario_modifico = request.user if request.user.is_authenticated else None
            empresa.save()
            form.save_m2m()
            return redirect('lista_empresas')
    else:
        form = EmpresaForm(instance=empresa)
    return render(request, 'configuraciones_maestras/editar_empresa.html', {'form': form, 'empresa': empresa})


@revisar_permiso('configuraciones_maestras.detalles_empresa')
def detalle_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_empresa.html', {'empresa': empresa})


@revisar_permiso('configuraciones_maestras.eliminar_empresa')
def eliminar_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        empresa.delete()
        return redirect('lista_empresas')
    return render(request, 'configuraciones_maestras/eliminar_empresa.html', {'empresa': empresa})


# CRUD Sucursal
@revisar_permiso('configuraciones_maestras.lista_sucursales')
def lista_sucursales(request):
    empresa_activa = Empresa.get_empresa_activa()
    sucursales = Sucursal.objects.filter(empresa=empresa_activa).order_by('nombre') if empresa_activa else Sucursal.objects.none()
    total_sucursales = sucursales.count()
    total_activas = sucursales.filter(activa=True).count()
    total_inactivas = total_sucursales - total_activas
    return render(request, 'configuraciones_maestras/lista_sucursales.html', {
        'sucursales': sucursales,
        'total_sucursales': total_sucursales,
        'total_activas': total_activas,
        'total_inactivas': total_inactivas,
    })


@revisar_permiso('configuraciones_maestras.agregar_sucursal')
def agregar_sucursal(request):
    empresa_activa = Empresa.get_empresa_activa()
    if empresa_activa is None:
        messages.warning(request, 'Primero debe crear la empresa activa antes de registrar sucursales.')
        return redirect('lista_empresas')
    if request.method == 'POST':
        form = SucursalForm(request.POST)
        if form.is_valid():
            sucursal = form.save(commit=False)
            sucursal.empresa = empresa_activa
            sucursal.usuario_modifico = request.user if request.user.is_authenticated else None
            sucursal.save()
            empresa_activa.sucursales.add(sucursal)
            messages.success(request, 'Sucursal registrada correctamente.')
            return redirect('lista_sucursales')
    else:
        form = SucursalForm()
    return render(request, 'configuraciones_maestras/agregar_sucursal.html', {'form': form})


@revisar_permiso('configuraciones_maestras.editar_sucursal')
def editar_sucursal(request, pk):
    sucursal = get_object_or_404(Sucursal, pk=pk)
    if request.method == 'POST':
        form = SucursalForm(request.POST, instance=sucursal)
        if form.is_valid():
            sucursal = form.save(commit=False)
            sucursal.usuario_modifico = request.user if request.user.is_authenticated else None
            sucursal.save()
            messages.success(request, 'Sucursal actualizada correctamente.')
            return redirect('lista_sucursales')
    else:
        form = SucursalForm(instance=sucursal)
    return render(request, 'configuraciones_maestras/editar_sucursal.html', {'form': form, 'sucursal': sucursal})


@revisar_permiso('configuraciones_maestras.detalles_sucursal')
def detalle_sucursal(request, pk):
    sucursal = get_object_or_404(Sucursal, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_sucursal.html', {'sucursal': sucursal})


@revisar_permiso('configuraciones_maestras.eliminar_sucursal')
def eliminar_sucursal(request, pk):
    sucursal = get_object_or_404(Sucursal, pk=pk)
    if request.method == 'POST':
        sucursal.delete()
        messages.success(request, 'Sucursal eliminada correctamente.')
        return redirect('lista_sucursales')
    return render(request, 'configuraciones_maestras/eliminar_sucursal.html', {'sucursal': sucursal})


# Maestro de Cajas operativas por Sucursal (el modelo vive en cobranzas;
# la apertura/cierre/saldos se manejan desde cobranzas, acá solo datos maestros)
def _caja_tiene_movimientos(caja):
    """Una caja con pagos o historial de aperturas/cierres no se puede eliminar."""
    return caja.pagos.exists() or caja.aperturas.exists() or caja.cierres.exists()


def _empleado_del_usuario(user):
    """Resuelve el Empleado asociado al usuario logueado (misma lógica que cobranzas)."""
    return getattr(getattr(user, 'perfil', None), 'empleado', None) or getattr(user, 'empleado', None)


@revisar_permiso('cobranzas.abrir_caja')
@transaction.atomic
def abrir_caja_operativa(request, sucursal_pk, pk):
    """Abre una caja operativa registrando el monto inicial (usa caja.abrir de cobranzas)."""
    sucursal = get_object_or_404(Sucursal, pk=sucursal_pk)
    caja = get_object_or_404(CajaOperativa, pk=pk, sucursal=sucursal)
    if caja.estado == 'abierta':
        messages.warning(request, 'La caja ya está abierta.')
        return redirect('lista_cajas', sucursal_pk=sucursal.pk)
    if request.method == 'POST':
        form = AperturaCajaOperativaForm(request.POST)
        if form.is_valid():
            empleado = _empleado_del_usuario(request.user)
            if not empleado:
                messages.error(request, 'No se pudo determinar el empleado asociado a este usuario.')
                return redirect('lista_cajas', sucursal_pk=sucursal.pk)
            caja.abrir(
                empleado=empleado,
                monto_inicial=form.cleaned_data['monto_inicial'],
                observaciones=form.cleaned_data.get('observaciones') or '',
            )
            AperturaCajaOperativa.objects.create(
                caja=caja,
                empleado=empleado,
                monto_inicial=form.cleaned_data['monto_inicial'],
                observaciones=form.cleaned_data.get('observaciones') or '',
            )
            messages.success(request, f'Caja abierta correctamente: {caja.nombre}')
            return redirect('lista_cajas', sucursal_pk=sucursal.pk)
    else:
        form = AperturaCajaOperativaForm()
    return render(request, 'configuraciones_maestras/abrir_caja_operativa.html', {
        'sucursal': sucursal,
        'caja': caja,
        'form': form,
    })


@revisar_permiso('cobranzas.cerrar_caja')
@transaction.atomic
def cerrar_caja_operativa(request, sucursal_pk, pk):
    """Cierra una caja operativa con arqueo (usa caja.cerrar de cobranzas)."""
    sucursal = get_object_or_404(Sucursal, pk=sucursal_pk)
    caja = get_object_or_404(CajaOperativa, pk=pk, sucursal=sucursal)
    if caja.estado != 'abierta':
        messages.warning(request, 'La caja ya está cerrada.')
        return redirect('lista_cajas', sucursal_pk=sucursal.pk)
    monto_esperado = caja.saldo_actual
    if request.method == 'POST':
        form = CierreCajaOperativaForm(request.POST)
        if form.is_valid():
            empleado = _empleado_del_usuario(request.user)
            if not empleado:
                messages.error(request, 'No se pudo determinar el empleado asociado a este usuario.')
                return redirect('lista_cajas', sucursal_pk=sucursal.pk)
            monto_real = form.cleaned_data['monto_real']
            caja.cerrar(
                empleado=empleado,
                monto_real=monto_real,
                observaciones=form.cleaned_data.get('observaciones') or '',
            )
            CierreCajaOperativa.objects.create(
                caja=caja,
                empleado=empleado,
                monto_esperado=monto_esperado,
                monto_real=monto_real,
                diferencia=monto_real - monto_esperado,
                observaciones=form.cleaned_data.get('observaciones') or '',
            )
            messages.success(request, f'Caja cerrada correctamente: {caja.nombre}')
            return redirect('lista_cajas', sucursal_pk=sucursal.pk)
    else:
        form = CierreCajaOperativaForm(initial={'monto_real': caja.saldo_actual})
    return render(request, 'configuraciones_maestras/cerrar_caja_operativa.html', {
        'sucursal': sucursal,
        'caja': caja,
        'form': form,
        'monto_esperado': monto_esperado,
    })


@revisar_permiso('configuraciones_maestras.lista_cajas')
def todas_las_cajas(request):
    """Acceso global a las cajas de todas las sucursales (punto de entrada del menú)."""
    cajas = CajaOperativa.objects.select_related('sucursal').all().order_by('sucursal__nombre', 'nombre')
    total_cajas = cajas.count()
    total_abiertas = cajas.filter(estado='abierta').count()
    total_cerradas = total_cajas - total_abiertas
    return render(request, 'configuraciones_maestras/todas_las_cajas.html', {
        'cajas': cajas,
        'total_cajas': total_cajas,
        'total_abiertas': total_abiertas,
        'total_cerradas': total_cerradas,
    })


@revisar_permiso('configuraciones_maestras.lista_cajas')
def lista_cajas(request, sucursal_pk):
    sucursal = get_object_or_404(Sucursal, pk=sucursal_pk)
    cajas = sucursal.cajas_operativas.all().order_by('nombre')
    total_cajas = cajas.count()
    total_abiertas = cajas.filter(estado='abierta').count()
    total_cerradas = total_cajas - total_abiertas
    return render(request, 'configuraciones_maestras/lista_cajas.html', {
        'sucursal': sucursal,
        'cajas': cajas,
        'total_cajas': total_cajas,
        'total_abiertas': total_abiertas,
        'total_cerradas': total_cerradas,
    })


@revisar_permiso('configuraciones_maestras.agregar_caja')
def agregar_caja(request, sucursal_pk):
    sucursal = get_object_or_404(Sucursal, pk=sucursal_pk)
    if request.method == 'POST':
        form = CajaForm(request.POST, sucursal=sucursal)
        if form.is_valid():
            caja = form.save(commit=False)
            caja.sucursal = sucursal
            caja.usuario_modifico = request.user if request.user.is_authenticated else None
            caja.save()
            messages.success(request, 'Caja registrada correctamente.')
            return redirect('lista_cajas', sucursal_pk=sucursal.pk)
    else:
        form = CajaForm(sucursal=sucursal)
    return render(request, 'configuraciones_maestras/agregar_caja.html', {'form': form, 'sucursal': sucursal})


@revisar_permiso('configuraciones_maestras.editar_caja')
def editar_caja(request, sucursal_pk, pk):
    sucursal = get_object_or_404(Sucursal, pk=sucursal_pk)
    caja = get_object_or_404(CajaOperativa, pk=pk, sucursal=sucursal)
    if caja.estado == 'abierta':
        messages.warning(request, 'No se puede editar una caja abierta. Ciérrela desde Caja (cobranzas) primero.')
        return redirect('lista_cajas', sucursal_pk=sucursal.pk)
    if request.method == 'POST':
        form = CajaForm(request.POST, instance=caja, sucursal=sucursal)
        if form.is_valid():
            caja = form.save(commit=False)
            caja.usuario_modifico = request.user if request.user.is_authenticated else None
            caja.save()
            messages.success(request, 'Caja actualizada correctamente.')
            return redirect('lista_cajas', sucursal_pk=sucursal.pk)
    else:
        form = CajaForm(instance=caja, sucursal=sucursal)
    return render(request, 'configuraciones_maestras/editar_caja.html', {'form': form, 'sucursal': sucursal, 'caja': caja})


@revisar_permiso('configuraciones_maestras.detalles_caja')
def detalle_caja(request, sucursal_pk, pk):
    sucursal = get_object_or_404(Sucursal, pk=sucursal_pk)
    caja = get_object_or_404(CajaOperativa, pk=pk, sucursal=sucursal)
    return render(request, 'configuraciones_maestras/detalle_caja.html', {
        'sucursal': sucursal,
        'caja': caja,
        'tiene_movimientos': _caja_tiene_movimientos(caja),
    })


@revisar_permiso('configuraciones_maestras.eliminar_caja')
def eliminar_caja(request, sucursal_pk, pk):
    sucursal = get_object_or_404(Sucursal, pk=sucursal_pk)
    caja = get_object_or_404(CajaOperativa, pk=pk, sucursal=sucursal)
    tiene_movimientos = _caja_tiene_movimientos(caja)
    if request.method == 'POST':
        if caja.estado == 'abierta':
            messages.warning(request, 'No se puede eliminar una caja abierta. Ciérrela desde Caja (cobranzas) primero.')
        elif tiene_movimientos:
            messages.warning(request, 'No se puede eliminar una caja con pagos o historial de aperturas/cierres.')
        else:
            caja.delete()
            messages.success(request, 'Caja eliminada correctamente.')
        return redirect('lista_cajas', sucursal_pk=sucursal.pk)
    return render(request, 'configuraciones_maestras/eliminar_caja.html', {
        'sucursal': sucursal,
        'caja': caja,
        'tiene_movimientos': tiene_movimientos,
    })


# CRUD Proveedor
@revisar_permiso('configuraciones_maestras.agregar_proveedor')
def agregar_proveedor(request):
    proveedor = Proveedor()
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        formset = ContactoProveedorFormSet(request.POST, instance=proveedor)
        if form.is_valid() and formset.is_valid():
            proveedor = form.save(commit=False)
            proveedor.save()
            contactos = formset.save(commit=False)
            for contacto in contactos:
                contacto.proveedor = proveedor
                contacto.save()
            for contacto in formset.deleted_objects:
                contacto.delete()
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm()
        formset = ContactoProveedorFormSet(instance=proveedor)
    return render(
        request,
        'configuraciones_maestras/agregar_proveedor.html',
        {'form': form, 'contact_formset': formset},
    )

@revisar_permiso('configuraciones_maestras.editar_proveedor')
def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        formset = ContactoProveedorFormSet(request.POST, instance=proveedor)
        if form.is_valid() and formset.is_valid():
            proveedor = form.save()
            contactos = formset.save(commit=False)
            for contacto in contactos:
                contacto.proveedor = proveedor
                contacto.save()
            for contacto in formset.deleted_objects:
                contacto.delete()
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)
        formset = ContactoProveedorFormSet(instance=proveedor)
    return render(
        request,
        'configuraciones_maestras/editar_proveedor.html',
        {'form': form, 'proveedor': proveedor, 'contact_formset': formset},
    )

@revisar_permiso('configuraciones_maestras.inactivar_proveedor')
def inactivar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.inactivar()
        return redirect('lista_proveedores')
    return render(request, 'configuraciones_maestras/inactivar_proveedor.html', {'proveedor': proveedor})

@revisar_permiso('configuraciones_maestras.eliminar_proveedor')
def eliminar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        if proveedor.eliminable():
            proveedor.delete()
        else:
            messages.error(request, 'No se puede eliminar este proveedor porque tiene contactos asociados.')
        return redirect('lista_proveedores')
    return render(request, 'configuraciones_maestras/eliminar_proveedor.html', {'proveedor': proveedor})

@revisar_permiso('configuraciones_maestras.detallar_proveedor')
def detalle_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    # Obtener repuestos asociados al proveedor para facilitar compras
    repuestos = Repuesto.objects.filter(proveedor=proveedor).only('id', 'nombre', 'stock_actual', 'costo_compra')
    # Ofrecer una lista de pedidos de abastecimiento existentes para asociación
    pedidos_abastecimiento = Pedido.objects.filter(tipo='abastecimiento').order_by('-fecha_pedido')[:20]
    return render(request, 'configuraciones_maestras/detalle_proveedor.html', {
        'proveedor': proveedor,
        'repuestos': repuestos,
        'pedidos_abastecimiento': pedidos_abastecimiento,
    })



@revisar_permiso('configuraciones_maestras.registrar_compra')
def comprar_repuesto_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method != 'POST':
        return redirect('detalle_proveedor', pk=pk)

    repuesto_ids = request.POST.getlist('repuesto_id')
    cantidades = request.POST.getlist('cantidad')
    precios = request.POST.getlist('precio_unitario')
    pedido_ids = request.POST.getlist('pedido_ids')
    numero_factura = request.POST.get('numero_factura')
    fecha_factura = request.POST.get('fecha_factura')
    observaciones = request.POST.get('observaciones', '').strip()
    factura_file = request.FILES.get('factura')

    if not repuesto_ids:
        messages.error(request, 'Debe seleccionar al menos un repuesto para registrar la compra.')
        return redirect('detalle_proveedor', pk=pk)

    items_data = []
    for index, repuesto_id in enumerate(repuesto_ids):
        if not repuesto_id:
            continue

        try:
            repuesto = Repuesto.objects.get(pk=repuesto_id, proveedor=proveedor)
        except Repuesto.DoesNotExist:
            messages.error(request, f'Repuesto con ID {repuesto_id} no existe para este proveedor.')
            return redirect('detalle_proveedor', pk=pk)

        cantidad = cantidades[index] if index < len(cantidades) else '1'
        precio_unitario = precios[index] if index < len(precios) else ''

        try:
            cantidad = int(cantidad or 1)
        except (ValueError, TypeError):
            cantidad = 1

        if cantidad <= 0:
            messages.error(request, 'La cantidad debe ser mayor que cero.')
            return redirect('detalle_proveedor', pk=pk)

        try:
            precio = Decimal(precio_unitario) if precio_unitario else repuesto.costo_compra or Decimal('0.00')
        except Exception:
            precio = repuesto.costo_compra or Decimal('0.00')

        items_data.append({
            'repuesto': repuesto,
            'cantidad': cantidad,
            'precio_unitario': precio,
        })

    if not items_data:
        messages.error(request, 'Debe agregar al menos un producto válido para registrar la factura.')
        return redirect('detalle_proveedor', pk=pk)

    factura = FacturaCompraProveedor.objects.create(
        proveedor=proveedor,
        numero_factura=numero_factura or None,
        fecha_factura=parse_date(fecha_factura) if fecha_factura else None,
        factura_pdf=factura_file,
        observaciones=observaciones or None,
    )

    for item_data in items_data:
        factura.items.create(
            repuesto=item_data['repuesto'],
            cantidad=item_data['cantidad'],
            precio_unitario=item_data['precio_unitario'],
        )

    factura.calcular_totales()

    pedidos_asociados = 0
    for pedido_id in pedido_ids:
        if not pedido_id:
            continue
        try:
            pedido = Pedido.objects.get(pk=pedido_id)
        except Pedido.DoesNotExist:
            continue

        factura.pedidos.add(pedido)
        pedido.proveedor_compra = proveedor
        if numero_factura:
            pedido.numero_factura = numero_factura
        if fecha_factura:
            pedido.fecha_factura = factura.fecha_factura
        if factura_file:
            pedido.factura_pdf = factura_file
        pedido.save(update_fields=['proveedor_compra', 'numero_factura', 'fecha_factura', 'factura_pdf'])
        pedidos_asociados += 1

    mensaje = f'Factura registrada con {len(items_data)} producto(s).'
    if pedidos_asociados:
        mensaje += f' Asociada a {pedidos_asociados} pedido(s).'
    else:
        mensaje += ' No se asoció a ningún pedido.'

    messages.success(request, mensaje)
    return redirect('detalle_proveedor', pk=pk)

# Listado de proveedores
@revisar_permiso('configuraciones_maestras.listar_proveedores')
def lista_proveedores(request):
    proveedores = Proveedor.objects.all()
    # filtro por estado y nombre
    if 'estado' in request.GET: 
        if request.GET['estado'] == 'ACTIVO':
            if 'nombre' in request.GET and request.GET['nombre']:
                proveedores = proveedores.filter(nombre__icontains=request.GET['nombre'], estado= True)
            else:
                proveedores = proveedores.filter(estado= True)
        elif request.GET['estado'] == 'INACTIVO':
            if 'nombre' in request.GET and request.GET['nombre']:
                proveedores = proveedores.filter(nombre__icontains=request.GET['nombre'], estado= False)
            else:
                proveedores = proveedores.filter(estado= False)
        else:
            if 'nombre' in request.GET and request.GET['nombre']:
                proveedores = proveedores.filter(nombre__icontains=request.GET['nombre'])
            
    return render(request, 'configuraciones_maestras/lista_proveedores.html', {'proveedores': proveedores})

# CRUD AgenteTransporte
@revisar_permiso('configuraciones_maestras.agregar_agente_transporte')
def agregar_agente_transporte(request):
    if request.method == 'POST':
        form = AgenteTransporteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_agentes_transporte')
    else:
        form = AgenteTransporteForm()
    return render(request, 'configuraciones_maestras/agregar_agente_transporte.html', {'form': form})

@revisar_permiso('configuraciones_maestras.editar_agente_transporte')
def editar_agente_transporte(request, pk):
    agente = get_object_or_404(AgenteTransporte, pk=pk)
    if request.method == 'POST':
        form = AgenteTransporteForm(request.POST, instance=agente)
        if form.is_valid():
            form.save()
            return redirect('lista_agentes_transporte')
    else:
        form = AgenteTransporteForm(instance=agente)
    return render(request, 'configuraciones_maestras/editar_agente_transporte.html', {'form': form, 'agente': agente})

@revisar_permiso('configuraciones_maestras.eliminar_agente_transporte')
def eliminar_agente_transporte(request, pk):
    agente = get_object_or_404(AgenteTransporte, pk=pk)
    if request.method == 'POST':
        agente.delete()
        return redirect('lista_agentes_transporte')
    return render(request, 'configuraciones_maestras/eliminar_agente_transporte.html', {'agente': agente})

@revisar_permiso('configuraciones_maestras.detallar_agente_transporte')
def detalle_agente_transporte(request, pk):
    agente = get_object_or_404(AgenteTransporte, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_agente_transporte.html', {'agente': agente})

# Listado de agentes de transporte
@revisar_permiso('configuraciones_maestras.listar_agentes_transporte')
def lista_agentes_transporte(request):
    # filtro por estado y nombre
    agentes = AgenteTransporte.objects.all()
    if 'estado' in request.GET:
        if request.GET['estado'] == 'ACTIVO':
            if 'nombre' in request.GET and request.GET['nombre']:
                agentes = agentes.filter(nombre__icontains=request.GET['nombre'], estado=True)
            else:
                agentes = agentes.filter(estado=True)
        elif request.GET['estado'] == 'INACTIVO':
            if 'nombre' in request.GET and request.GET['nombre']:
                agentes = agentes.filter(nombre__icontains=request.GET['nombre'], estado=False)
            else:
                agentes = agentes.filter(estado=False)
        else:
            if 'nombre' in request.GET and request.GET['nombre']:
                agentes = agentes.filter(nombre__icontains=request.GET['nombre'])

    return render(request, 'configuraciones_maestras/lista_agentes_transporte.html', {'agentes': agentes})

# CRUD DespachanteAduana
@revisar_permiso('configuraciones_maestras.agregar_despachante_aduana')
def agregar_despachante_aduana(request):
    if request.method == 'POST':
        form = DespachanteAduanaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_despachantes_aduana')
    else:
        form = DespachanteAduanaForm()
    return render(request, 'configuraciones_maestras/agregar_despachante_aduana.html', {'form': form})

@revisar_permiso('configuraciones_maestras.editar_despachante_aduana')
def editar_despachante_aduana(request, pk):
    despachante = get_object_or_404(DespachanteAduana, pk=pk)
    if request.method == 'POST':
        form = DespachanteAduanaForm(request.POST, instance=despachante)
        if form.is_valid():
            form.save()
            return redirect('lista_despachantes_aduana')
    else:
        form = DespachanteAduanaForm(instance=despachante)
    return render(request, 'configuraciones_maestras/editar_despachante_aduana.html', {'form': form, 'despachante': despachante})

@revisar_permiso('configuraciones_maestras.eliminar_despachante_aduana')
def eliminar_despachante_aduana(request, pk):
    despachante = get_object_or_404(DespachanteAduana, pk=pk)
    if request.method == 'POST':
        despachante.delete()
        return redirect('lista_despachantes_aduana')
    return render(request, 'configuraciones_maestras/eliminar_despachante_aduana.html', {'despachante': despachante})

@revisar_permiso('configuraciones_maestras.detallar_despachante_aduana')
def detalle_despachante_aduana(request, pk):
    despachante = get_object_or_404(DespachanteAduana, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_despachante_aduana.html', {'despachante': despachante})


# CRUD Moneda
@revisar_permiso('configuraciones_maestras.listar_monedas')
def lista_monedas(request):
    MonedaFacade.ensure_defaults()
    monedas = Moneda.objects.all().order_by('codigo')
    return render(request, 'configuraciones_maestras/lista_monedas.html', {'monedas': monedas})


@revisar_permiso('configuraciones_maestras.agregar_moneda')
def agregar_moneda(request):
    if request.method == 'POST':
        form = MonedaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_monedas')
    else:
        form = MonedaForm()
    return render(request, 'configuraciones_maestras/agregar_moneda.html', {'form': form})


@revisar_permiso('configuraciones_maestras.editar_moneda')
def editar_moneda(request, pk):
    moneda = get_object_or_404(Moneda, pk=pk)
    if request.method == 'POST':
        form = MonedaForm(request.POST, instance=moneda)
        if form.is_valid():
            form.save()
            return redirect('lista_monedas')
    else:
        form = MonedaForm(instance=moneda)
    return render(request, 'configuraciones_maestras/editar_moneda.html', {'form': form, 'moneda': moneda})


@revisar_permiso('configuraciones_maestras.detalle_moneda')
def detalle_moneda(request, pk):
    moneda = get_object_or_404(Moneda, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_moneda.html', {'moneda': moneda})


@revisar_permiso('configuraciones_maestras.eliminar_moneda')
def eliminar_moneda(request, pk):
    moneda = get_object_or_404(Moneda, pk=pk)
    if request.method == 'POST':
        moneda.delete()
        return redirect('lista_monedas')
    return render(request, 'configuraciones_maestras/eliminar_moneda.html', {'moneda': moneda})

# Listado de despachantes de aduana
@revisar_permiso('configuraciones_maestras.listar_despachantes_aduana')
def lista_despachantes_aduana(request):
    despachantes = DespachanteAduana.objects.all()
    return render(request, 'configuraciones_maestras/lista_despachantes_aduana.html', {'despachantes': despachantes})

# CRUD Despachante
@revisar_permiso('configuraciones_maestras.agregar_despachante')
def agregar_despachante(request):
    if request.method == 'POST':
        form = DespachanteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Despachante creado exitosamente.')
            return redirect('lista_despachantes')
    else:
        form = DespachanteForm()
    return render(request, 'configuraciones_maestras/agregar_despachante.html', {'form': form})

@revisar_permiso('configuraciones_maestras.editar_despachante')
def editar_despachante(request, pk):
    despachante = get_object_or_404(Despachante, pk=pk)
    if request.method == 'POST':
        form = DespachanteForm(request.POST, instance=despachante)
        if form.is_valid():
            form.save()
            messages.success(request, 'Despachante actualizado exitosamente.')
            return redirect('lista_despachantes')
    else:
        form = DespachanteForm(instance=despachante)
    return render(request, 'configuraciones_maestras/editar_despachante.html', {'form': form, 'despachante': despachante})

@revisar_permiso('configuraciones_maestras.eliminar_despachante')
def eliminar_despachante(request, pk):
    despachante = get_object_or_404(Despachante, pk=pk)
    if request.method == 'POST':
        despachante.delete()
        messages.success(request, 'Despachante eliminado exitosamente.')
        return redirect('lista_despachantes')
    return render(request, 'configuraciones_maestras/eliminar_despachante.html', {'despachante': despachante})

@revisar_permiso('configuraciones_maestras.detallar_despachante')
def detalle_despachante(request, pk):
    despachante = get_object_or_404(Despachante, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_despachante.html', {'despachante': despachante})

@revisar_permiso('configuraciones_maestras.listar_despachantes')
def lista_despachantes(request):
    despachantes = Despachante.objects.all()
    # Filtrado por estado y país
    if 'estado' in request.GET:
        if request.GET['estado'] == 'ACTIVO':
            despachantes = despachantes.filter(es_activo=True)
        elif request.GET['estado'] == 'INACTIVO':
            despachantes = despachantes.filter(es_activo=False)
    
    if 'pais' in request.GET and request.GET['pais']:
        despachantes = despachantes.filter(pais_codigo=request.GET['pais'])
    
    if 'nombre' in request.GET and request.GET['nombre']:
        despachantes = despachantes.filter(nombre_razon_social__icontains=request.GET['nombre'])
    
    return render(request, 'configuraciones_maestras/lista_despachantes.html', {'despachantes': despachantes})

# CRUD TasaCambio
@revisar_permiso('configuraciones_maestras.agregar_tasa_cambio')
def agregar_tasa_cambio(request):
    if request.method == 'POST':
        form = TasaCambioForm(request.POST)
        if form.is_valid():
            tasa = form.save(commit=False)
            tasa.usuario_creo = request.user
            tasa.save()
            return redirect('lista_tasas_cambio')
    else:
        form = TasaCambioForm()
    return render(request, 'configuraciones_maestras/agregar_tasa_cambio.html', {'form': form})

@revisar_permiso('configuraciones_maestras.editar_tasa_cambio')
def editar_tasa_cambio(request, pk):
    tasa = get_object_or_404(TasaCambio, pk=pk)
    if request.method == 'POST':
        form = TasaCambioForm(request.POST, instance=tasa)
        if form.is_valid():
            form.save()
            return redirect('lista_tasas_cambio')
    else:
        form = TasaCambioForm(instance=tasa)
    return render(request, 'configuraciones_maestras/editar_tasa_cambio.html', {'form': form, 'tasa': tasa})

@revisar_permiso('configuraciones_maestras.eliminar_tasa_cambio')
def eliminar_tasa_cambio(request, pk):
    tasa = get_object_or_404(TasaCambio, pk=pk)
    if request.method == 'POST':
        tasa.delete()
        return redirect('lista_tasas_cambio')
    return render(request, 'configuraciones_maestras/eliminar_tasa_cambio.html', {'tasa': tasa})

@revisar_permiso('configuraciones_maestras.detallar_tasa_cambio')
def detalle_tasa_cambio(request, pk):
    tasa = get_object_or_404(TasaCambio, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_tasa_cambio.html', {'tasa': tasa})

# Listado de tasas de cambio
@revisar_permiso('configuraciones_maestras.listar_tasas_cambio')
def lista_tasas_cambio(request):
    tasas = TasaCambio.objects.all()
    tasa_actual = TasaCambioFacade.obtener_tasa_actual()
    existe_tasa_hoy = TasaCambioFacade.existe_tasa_para_hoy()
    return render(request, 'configuraciones_maestras/lista_tasas_cambio.html', {
        'tasas': tasas,
        'tasa_actual': tasa_actual,
        'existe_tasa_hoy': existe_tasa_hoy
    })

@revisar_permiso('configuraciones_maestras.listar_monedas')
def lista_monedas(request):
    monedas = Moneda.objects.all()
    return render(request, 'configuraciones_maestras/lista_monedas.html', {'monedas': monedas})

@revisar_permiso('configuraciones_maestras.agregar_moneda')
def agregar_moneda(request):
    if request.method == 'POST':
        form = MonedaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Moneda creada correctamente.')
            return redirect('lista_monedas')
    else:
        form = MonedaForm()
    return render(request, 'configuraciones_maestras/agregar_moneda.html', {'form': form})

@revisar_permiso('configuraciones_maestras.editar_moneda')
def editar_moneda(request, pk):
    moneda = get_object_or_404(Moneda, pk=pk)
    if request.method == 'POST':
        form = MonedaForm(request.POST, instance=moneda)
        if form.is_valid():
            form.save()
            messages.success(request, 'Moneda actualizada correctamente.')
            return redirect('lista_monedas')
    else:
        form = MonedaForm(instance=moneda)
    return render(request, 'configuraciones_maestras/editar_moneda.html', {'form': form, 'moneda': moneda})

@revisar_permiso('configuraciones_maestras.eliminar_moneda')
def eliminar_moneda(request, pk):
    moneda = get_object_or_404(Moneda, pk=pk)
    if request.method == 'POST':
        moneda.delete()
        messages.success(request, 'Moneda eliminada correctamente.')
        return redirect('lista_monedas')
    return render(request, 'configuraciones_maestras/eliminar_moneda.html', {'moneda': moneda})

@revisar_permiso('configuraciones_maestras.detallar_moneda')
def detalle_moneda(request, pk):
    moneda = get_object_or_404(Moneda, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_moneda.html', {'moneda': moneda})

# --------------------------------------------------------------------------
# Vista de Departamentos
# --------------------------------------------------------------------------

@revisar_permiso('configuraciones_maestras.listar_departamentos')
def lista_departamentos(request):
    empresa_activa = Empresa.get_empresa_activa()
    departamentos = Departamento.objects.filter(empresa=empresa_activa) if empresa_activa else Departamento.objects.none()
    return render(request, 'configuraciones_maestras/lista_departamentos.html', {'departamentos': departamentos})

@revisar_permiso('configuraciones_maestras.agregar_departamento')
def agregar_departamento(request):
    empresa_activa = Empresa.get_empresa_activa()
    if empresa_activa is None:
        messages.warning(request, 'Primero debe crear la empresa activa antes de registrar dependencias.')
        return redirect('lista_empresas')
    if request.method == 'POST':
        form = DepartamentoForm(request.POST)
        if form.is_valid():
            departamento = form.save(commit=False)
            departamento.empresa = empresa_activa
            departamento.save()
            return redirect('lista_departamentos')
    else:
        form = DepartamentoForm()
    return render(request, 'configuraciones_maestras/agregar_departamento.html', {'form': form})

@revisar_permiso('configuraciones_maestras.editar_departamento')
def editar_departamento(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    if request.method == 'POST':
        form = DepartamentoForm(request.POST, instance=departamento)
        if form.is_valid():
            if not departamento.editable():
                messages.error(request, 'No se puede editar este departamento porque tiene cargos asociados que no son eliminables.')
                return redirect('lista_departamentos')
            form.save()
            return redirect('lista_departamentos')
    else:
        form = DepartamentoForm(instance=departamento)
    return render(request, 'configuraciones_maestras/editar_departamento.html', {'form': form, 'departamento': departamento})

@revisar_permiso('configuraciones_maestras.eliminar_departamento')
def eliminar_departamento(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    if request.method == 'POST':
        if departamento.eliminable():
            departamento.delete()
        else:
            messages.error(request, 'No se puede eliminar este departamento porque tiene empleados asociados.')
        return redirect('lista_departamentos')
    return render(request, 'configuraciones_maestras/eliminar_departamento.html', {'departamento': departamento})

@revisar_permiso('configuraciones_maestras.detallar_departamento')
def detalle_departamento(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_departamento.html', {'departamento': departamento})

#desactivar departamento
@revisar_permiso('configuraciones_maestras.inactivar_departamento')
def inactivar_departamento(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    if request.method == 'POST':
        if not departamento.inactivable():
            messages.error(request, 'No se puede inactivar este departamento porque tiene cargos asociados que no son eliminables.')
            return redirect('lista_departamentos')
        departamento.inactivar()
        return redirect('lista_departamentos')
    return render(request, 'configuraciones_maestras/inactivar_departamento.html', {'departamento': departamento})

# activar departamento
@revisar_permiso('configuraciones_maestras.activar_departamento')
def activar_departamento(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    if request.method == 'POST':
        if not departamento.activable():
            messages.error(request, 'No se puede activar este departamento porque tiene cargos asociados que no son eliminables.')
            return redirect('lista_departamentos')
        departamento.activar()
        return redirect('lista_departamentos')
    return render(request, 'configuraciones_maestras/activar_departamento.html', {'departamento': departamento})


# --------------------------------------------------------------------------
# Vista de Cargos
# --------------------------------------------------------------------------

@revisar_permiso('configuraciones_maestras.listar_cargos')
def lista_cargos(request):
    cargos = Cargo.objects.all()
    return render(request, 'configuraciones_maestras/lista_cargos.html', {'cargos': cargos})

@revisar_permiso('configuraciones_maestras.agregar_cargo')
def agregar_cargo(request):
    if request.method == 'POST':
        form = CargoForm(request.POST)
        if form.is_valid():
            cargo = form.save(commit=False)
            cargo.save()
            cargo.roles.set(form.cleaned_data.get('roles', []))
            return redirect('lista_cargos')
    else:
        form = CargoForm()
    return render(request, 'configuraciones_maestras/agregar_cargo.html', {'form': form})

@revisar_permiso('configuraciones_maestras.editar_cargo')
def editar_cargo(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    if request.method == 'POST':
        form = CargoForm(request.POST, instance=cargo)
        if form.is_valid():
            if not cargo.editable():
                messages.error(request, 'No se puede editar este cargo porque tiene empleados asociados que no son eliminables.')
                return redirect('lista_cargos')
            cargo = form.save(commit=False)
            cargo.save()
            cargo.roles.set(form.cleaned_data.get('roles', []))
            return redirect('lista_cargos')
    else:
        form = CargoForm(instance=cargo)
    return render(request, 'configuraciones_maestras/editar_cargo.html', {'form': form, 'cargo': cargo})

@revisar_permiso('configuraciones_maestras.eliminar_cargo')
def eliminar_cargo(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    eliminable = cargo.eliminable()
    if request.method == 'POST':
        if eliminable:
            cargo.delete()
            return redirect('lista_cargos')
        messages.error(request, 'No se puede eliminar este cargo porque tiene empleados asociados.')
    return render(request, 'configuraciones_maestras/eliminar_cargo.html', {'cargo': cargo, 'eliminable': eliminable})

@revisar_permiso('configuraciones_maestras.detallar_cargo')
def detalle_cargo(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_cargo.html', {'cargo': cargo})

# activar cargo
@revisar_permiso('configuraciones_maestras.activar_cargo')
def activar_cargo(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    if request.method == 'POST':
        if not cargo.activable():
            messages.error(request, 'No se puede activar este cargo porque tiene empleados asociados que no son eliminables.')
            return redirect('lista_cargos')
        cargo.activar()
        return redirect('lista_cargos')
    return render(request, 'configuraciones_maestras/activar_cargo.html', {'cargo': cargo})

# desactivar cargo
@revisar_permiso('configuraciones_maestras.inactivar_cargo')
def inactivar_cargo(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    if request.method == 'POST':
        if not cargo.inactivable():
            messages.error(request, 'No se puede inactivar este cargo porque tiene empleados asociados que no son eliminables.')
            return redirect('lista_cargos')
        cargo.inactivar()
        return redirect('lista_cargos')
    return render(request, 'configuraciones_maestras/inactivar_cargo.html', {'cargo': cargo})


permisos_iniciales_configuraciones_maestras = [
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
        }

    ]
