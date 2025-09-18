from django.shortcuts import render
from .forms import SolicitudReposicionForm, ItemSolicitudFormSet
from .models import SolicitudReposicion

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

def listar_solicitudes_reposicion(request):
    solicitudes = SolicitudReposicion.objects.all()
    return render(request, "reposicion_stock/listar_solicitudes.html", {"solicitudes": solicitudes})

def detalle_solicitud_reposicion(request, pk):
    solicitud = SolicitudReposicion.objects.get(pk=pk)
    items = solicitud.items_solicitados.all()
    return render(request, "reposicion_stock/detalle_solicitud.html", {"solicitud": solicitud, "items": items})

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

def eliminar_solicitud_reposicion(request, pk):
    solicitud = SolicitudReposicion.objects.get(pk=pk)
    if request.method == "POST":
        solicitud.delete()
        # Redirigir a una página de éxito o mostrar un mensaje
    return render(request, "reposicion_stock/eliminar_solicitud.html", {"solicitud": solicitud})

def aprobar_solicitud_reposicion(request, pk):
    solicitud = SolicitudReposicion.objects.get(pk=pk)
    if request.method == "POST":
        solicitud.estado = 'APROBADA'
        solicitud.save()
        # Redirigir a una página de éxito o mostrar un mensaje
    return render(request, "reposicion_stock/aprobar_solicitud.html", {"solicitud": solicitud})

def rechazar_solicitud_reposicion(request, pk):
    solicitud = SolicitudReposicion.objects.get(pk=pk)
    if request.method == "POST":
        solicitud.estado = 'RECHAZADA'
        solicitud.save()
        # Redirigir a una página de éxito o mostrar un mensaje
    return render(request, "reposicion_stock/rechazar_solicitud.html", {"solicitud": solicitud})

def completar_solicitud_reposicion(request, pk):
    solicitud = SolicitudReposicion.objects.get(pk=pk)
    if request.method == "POST":
        solicitud.estado = 'COMPLETADA'
        solicitud.save()
        # Redirigir a una página de éxito o mostrar un mensaje
    return render(request, "reposicion_stock/completar_solicitud.html", {"solicitud": solicitud})

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
