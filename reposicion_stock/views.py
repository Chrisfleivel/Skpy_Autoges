from django.shortcuts import render
from .forms import SolicitudReposicionForm, ItemSolicitudFormSet
from .models import SolicitudReposicion
# revisar_permiso
from seguridad_usuarios.decorators import revisar_permiso

@revisar_permiso('reposicion_stock.agregar_solicitud_de_reposicion')
def agregar_solicitud_reposicion(request):
    if request.method == "POST":
        form = SolicitudReposicionForm(request.POST)
        formset = ItemSolicitudFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            solicitud = form.save()
            items = formset.save(commit=False)
            for item in items:
                item.solicitud = solicitud
                item.save()
            # Redirigir a una página de éxito o mostrar un mensaje
    else:
        form = SolicitudReposicionForm()
        formset = ItemSolicitudFormSet()
    return render(request, "reposicion_stock/agregar_solicitud.html", {"form": form, "formset": formset})

@revisar_permiso('reposicion_stock.listar_solicitudes_de_reposicion')
def listar_solicitudes_reposicion(request):
    solicitudes = SolicitudReposicion.objects.all()
    return render(request, "reposicion_stock/listar_solicitudes.html", {"solicitudes": solicitudes})

@revisar_permiso('reposicion_stock.detallar_solicitud_de_reposicion')
def detalle_solicitud_reposicion(request, pk):
    solicitud = SolicitudReposicion.objects.get(pk=pk)
    items = solicitud.items_solicitados.all()
    return render(request, "reposicion_stock/detalle_solicitud.html", {"solicitud": solicitud, "items": items})

@revisar_permiso('reposicion_stock.editar_solicitud_de_reposicion')
def editar_solicitud_reposicion(request, pk):
    solicitud = SolicitudReposicion.objects.get(pk=pk)
    if request.method == "POST":
        form = SolicitudReposicionForm(request.POST, instance=solicitud)
        formset = ItemSolicitudFormSet(request.POST, instance=solicitud)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            # Redirigir a una página de éxito o mostrar un mensaje
    else:
        form = SolicitudReposicionForm(instance=solicitud)
        formset = ItemSolicitudFormSet(instance=solicitud)
    return render(request, "reposicion_stock/editar_solicitud.html", {"form": form, "formset": formset, "solicitud": solicitud})

@revisar_permiso('reposicion_stock.eliminar_solicitud_de_reposicion')
def eliminar_solicitud_reposicion(request, pk):
    solicitud = SolicitudReposicion.objects.get(pk=pk)
    if request.method == "POST":
        solicitud.delete()
        # Redirigir a una página de éxito o mostrar un mensaje
    return render(request, "reposicion_stock/eliminar_solicitud.html", {"solicitud": solicitud})

@revisar_permiso('reposicion_stock.aprobar_solicitud_de_reposicion')
def aprobar_solicitud_reposicion(request, pk):
    solicitud = SolicitudReposicion.objects.get(pk=pk)
    if request.method == "POST":
        solicitud.estado = 'APROBADA'
        solicitud.save()
        # Redirigir a una página de éxito o mostrar un mensaje
    return render(request, "reposicion_stock/aprobar_solicitud.html", {"solicitud": solicitud})

@revisar_permiso('reposicion_stock.rechazar_solicitud_de_reposicion')
def rechazar_solicitud_reposicion(request, pk):
    solicitud = SolicitudReposicion.objects.get(pk=pk)
    if request.method == "POST":
        solicitud.estado = 'RECHAZADA'
        solicitud.save()
        # Redirigir a una página de éxito o mostrar un mensaje
    return render(request, "reposicion_stock/rechazar_solicitud.html", {"solicitud": solicitud})

@revisar_permiso('reposicion_stock.completar_solicitud_de_reposicion')
def completar_solicitud_reposicion(request, pk):
    solicitud = SolicitudReposicion.objects.get(pk=pk)
    if request.method == "POST":
        solicitud.estado = 'COMPLETADA'
        solicitud.save()
        # Redirigir a una página de éxito o mostrar un mensaje
    return render(request, "reposicion_stock/completar_solicitud.html", {"solicitud": solicitud})

@revisar_permiso('reposicion_stock.cancelar_solicitud_de_reposicion')
def cancelar_solicitud_reposicion(request, pk):
    solicitud = SolicitudReposicion.objects.get(pk=pk)
    if request.method == "POST":
        solicitud.estado = 'CANCELADA'
        solicitud.save()
        # Redirigir a una página de éxito o mostrar un mensaje
    return render(request, "reposicion_stock/cancelar_solicitud.html", {"solicitud": solicitud})

def historial_solicitudes_reposicion(request):
    solicitudes = SolicitudReposicion.objects.all().order_by('-fecha_solicitud')
    return render(request, "reposicion_stock/historial_solicitudes.html", {"solicitudes": solicitudes})



# --------------------------------------------------------------------------
# Vistas para gestionar Solicitudes de Reposición de Stock
# --------------------------------------------------------------------------
# Estas vistas permiten crear, listar, ver detalles y editar solicitudes de reposición.
# Puedes personalizarlas según las necesidades específicas de tu aplicación,    
# incluyendo permisos, validaciones adicionales y lógica de negocio.
# Asegúrate de crear las plantillas HTML correspondientes en la carpeta


permisos_iniciales_reposicion_stock = [
    {
        'codename': 'reposicion_stock.listar_solicitudes_de_reposicion',
        'nombre': 'Listar Solicitudes de Reposición',
        'descripcion': 'Permite agregar un nueva solicitud de reposición de stock.'
    },
    {
        'codename': 'reposicion_stock.agregar_solicitud_de_reposicion',
        'nombre': 'Agregar Solicitud de Reposición',
        'descripcion': 'Permite agregar un nueva solicitud de reposición de stock.'
    },
    {
        'codename': 'reposicion_stock.detallar_solicitud_de_reposicion',
        'nombre': 'Detalle de Solicitud de Reposición',
        'descripcion': 'Permite ver los detalles de una solicitud de reposición de stock.'
    },
    {
        'codename': 'reposicion_stock.editar_solicitud_de_reposicion',
        'nombre': 'Editar Solicitud de Reposición',
        'descripcion': 'Permite editar una solicitud de reposición de stock.'
    },
    {
        'codename': 'reposicion_stock.eliminar_solicitud_de_reposicion',
        'nombre': 'Eliminar Solicitud de Reposición',
        'descripcion': 'Permite eliminar una solicitud de reposición de stock.'
    },
    {
        'codename': 'reposicion_stock.aprobar_solicitud_de_reposicion',
        'nombre': 'Aprobar Solicitud de Reposición',
        'descripcion': 'Permite aprobar una solicitud de reposición de stock.'
    },
    {
        'codename': 'reposicion_stock.rechazar_solicitud_de_reposicion',
        'nombre': 'Rechazar Solicitud de Reposición',
        'descripcion': 'Permite rechazar una solicitud de reposición de stock.'
    },
    {
        'codename': 'reposicion_stock.completar_solicitud_de_reposicion',
        'nombre': 'Completar Solicitud de Reposición',
        'descripcion': 'Permite marcar una solicitud de reposición como completada.'
    },
    {
        'codename': 'reposicion_stock.cancelar_solicitud_de_reposicion',
        'nombre': 'Cancelar Solicitud de Reposición',
        'descripcion': 'Permite cancelar una solicitud de reposición de stock.',
        'sector': 'Reposición de Stock'
    },
]