# clientes_pedidos/admin.py
from django.contrib import admin
from .models import Cliente, Pedido, ItemPedido, Cotizacion

admin.site.register(Cliente)
admin.site.register(Pedido)
admin.site.register(ItemPedido)
admin.site.register(Cotizacion)
