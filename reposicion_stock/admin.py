from django.contrib import admin
from .models import SolicitudReposicion, ItemSolicitudReposicion
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode
from seguridad_usuarios.models import UsuarioPerfil
from inventario.models import Vehiculo, Repuesto
from seguridad_usuarios.admin import UsuarioPerfilAdmin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Q
from .models import SolicitudReposicion, ItemSolicitud
from seguridad_usuarios.models import UsuarioPerfil

# --------------------------------------------------------------------------
# Filtros personalizados para el admin
# --------------------------------------------------------------------------
class EstadoSolicitudFilter(SimpleListFilter):
    title = 'Estado de la Solicitud'
    parameter_name = 'estado'

    def lookups(self, request, model_admin):
        return SolicitudReposicion.ESTADO_SOLICITUD

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(estado=self.value())
        return queryset

# --------------------------------------------------------------------------
# Inline para los ítems de la solicitud
# --------------------------------------------------------------------------
class ItemSolicitudInline(admin.TabularInline):
    model = ItemSolicitud
    extra = 1
    fields = ('vehiculo', 'repuesto', 'cantidad', 'comentario_item', 'precio_unitario', 'costo_unitario')
    autocomplete_fields = ['vehiculo', 'repuesto']
    readonly_fields = []
    show_change_link = True 
    can_delete = True

# --------------------------------------------------------------------------
# Admin para SolicitudReposicion
# --------------------------------------------------------------------------

@admin.register(SolicitudReposicion)
class SolicitudReposicionAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_creacion', 'creador_link', 'estado', 'observaciones', 'total_items')
    list_filter = (EstadoSolicitudFilter, 'fecha_creacion', 'creador')
    search_fields = ('id', 'creador__user__username', 'creador__user__first_name', 'creador__user__last_name')
    readonly_fields = ('fecha_creacion', 'creador')
    inlines = [ItemSolicitudInline]
    actions = ['mark_as_enviada', 'mark_as_consolidada', 'mark_as_completada', 'mark_as_cancelada']

    def creador_link(self, obj):
        if obj.creador:
            url = reverse('admin:seguridad_usuarios_usuarioperfil_change', args=[obj.creador.pk])
            return format_html('<a href="{}">{}</a>', url, obj.creador.user.username)
        return "-"
    creador_link.short_description = 'Creador'
    creador_link.admin_order_field = 'creador__user__username'

    def total_items(self, obj):
        return obj.items_solicitados.count()
    total_items.short_description = 'Total de Ítems'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creador = UsuarioPerfil.objects.get(user=request.user)
        super().save_model(request, obj, form, change)

    def mark_as_enviada(self, request, queryset):
        updated = queryset.update(estado='enviada')
        self.message_user(request, f"{updated} solicitud(es) marcada(s) como Enviada.")
    mark_as_enviada.short_description = "Marcar como Enviada"

    def mark_as_consolidada(self, request, queryset):
        updated = queryset.update(estado='consolidada')
        self.message_user(request, f"{updated} solicitud(es) marcada(s) como Consolidada.")
    mark_as_consolidada.short_description = "Marcar como Consolidada"

    def mark_as_completada(self, request, queryset):
        updated = queryset.update(estado='completada')
        self.message_user(request, f"{updated} solicitud(es) marcada(s) como Completada.")
    mark_as_completada.short_description = "Marcar como Completada"

    def mark_as_cancelada(self, request, queryset):
        updated = queryset.update(estado='cancelada')
        self.message_user(request, f"{updated} solicitud(es) marcada(s) como Cancelada.")
    mark_as_cancelada.short_description = "Marcar como Cancelada"
