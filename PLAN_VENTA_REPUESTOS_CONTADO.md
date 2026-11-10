# Plan de Implementación: Venta de Repuestos al Contado con Reserva de Stock

## Contexto Actual
- Modelo `Repuesto`: tiene `stock_actual`, `stock_minimo`, `precio_venta`
- Modelo `Pedido`: es FSM con estados incluyendo `facturado_contado`
- Modelo `ItemPedido`: relaciona pedidos con repuestos/vehículos
- El método `confirmar_entrega_repuesto` reduce stock al entregar

## Problemas a Resolver
1. ❌ No hay sistema de reserva de stock cuando se crea el pedido
2. ❌ Se pueden vender unidades a múltiples clientes si no hay suficiente stock
3. ❌ El stock no se reduce automáticamente al facturar contado
4. ❌ No hay trazabilidad de qué stock está "comprometido" en pedidos

## Solución Propuesta

### 1. Agregar Campo de Stock Reservado a `Repuesto`
```python
class Repuesto(Producto):
    stock_actual = models.PositiveIntegerField(default=0)
    stock_reservado = models.PositiveIntegerField(default=0, verbose_name="Stock Reservado")
    stock_minimo = models.PositiveIntegerField(default=0)
    
    @property
    def stock_disponible(self):
        """Stock real disponible sin reservas"""
        return self.stock_actual - self.stock_reservado
    
    def puede_reservar(self, cantidad):
        """Verifica si hay stock disponible para reservar"""
        return self.stock_disponible >= cantidad
    
    def reservar(self, cantidad):
        """Reserva stock para un pedido"""
        if not self.puede_reservar(cantidad):
            raise ValidationError(f"Stock insuficiente. Disponible: {self.stock_disponible}")
        self.stock_reservado += cantidad
        self.save(update_fields=['stock_reservado'])
    
    def liberar_reserva(self, cantidad):
        """Libera reserva si se cancela el pedido"""
        self.stock_reservado = max(0, self.stock_reservado - cantidad)
        self.save(update_fields=['stock_reservado'])
    
    def confirmar_venta(self, cantidad):
        """Confirma la venta: reduce stock_actual y stock_reservado"""
        self.stock_reservado = max(0, self.stock_reservado - cantidad)
        self.stock_actual = max(0, self.stock_actual - cantidad)
        self.save(update_fields=['stock_actual', 'stock_reservado'])
```

### 2. Crear Modelo de Reserva (Trazabilidad)
```python
class ReservaRepuesto(models.Model):
    """Rastreo de reservas de repuestos por pedido"""
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE, related_name='reservas')
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='reservas_repuestos')
    item_pedido = models.ForeignKey(ItemPedido, on_delete=models.CASCADE, related_name='reservas')
    cantidad_reservada = models.PositiveIntegerField()
    cantidad_vendida = models.PositiveIntegerField(default=0)
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('reservada', 'Reservada'),
            ('vendida', 'Vendida'),
            ('cancelada', 'Cancelada'),
        ],
        default='reservada'
    )
    
    def confirmar_venta(self):
        """Convierte la reserva en venta"""
        self.cantidad_vendida = self.cantidad_reservada
        self.estado = 'vendida'
        self.save(update_fields=['cantidad_vendida', 'estado'])
    
    def cancelar(self):
        """Cancela la reserva"""
        self.estado = 'cancelada'
        self.save(update_fields=['estado'])
```

### 3. Modificar `ItemPedido` para Soportar Reservas
- Agregar método `crear_reserva()` al crear items de repuesto
- Verificar disponibilidad antes de guardar el item

### 4. Automatizar en el Flujo de Pedidos
```python
class Pedido:
    @transition(field='estado', source=..., target='facturado_contado')
    def facturar_pedido_venta_contado(self):
        """Factura y reduce stock automáticamente"""
        if self.tipo != 'venta':
            raise ValidationError('Solo se factura pedidos de venta.')
        
        # Para repuestos: confirmar venta de reservas
        for item in self.items.filter(tipo_producto='repuesto'):
            if item.repuesto:
                # Obtener reserva asociada
                reserva = item.reservas.filter(estado='reservada').first()
                if reserva:
                    reserva.confirmar_venta()
                    # Reduce stock real
                    item.repuesto.confirmar_venta(item.cantidad)
                else:
                    # Si no hay reserva, hacer venta directa
                    if item.cantidad > item.repuesto.stock_disponible:
                        raise ValidationError(
                            f"Stock insuficiente para {item.repuesto}. "
                            f"Disponible: {item.repuesto.stock_disponible}"
                        )
                    item.repuesto.confirmar_venta(item.cantidad)
        
        self.estado = 'facturado_contado'
        self.save(update_fields=['estado'])
```

### 5. Actualizar Formularios
- En el formulario de crear pedido de venta: verificar stock disponible
- Mostrar advertencia si hay poco stock
- Validar que hay stock al crear el ItemPedido

### 6. Migrations
```bash
python manage.py makemigrations inventario
python manage.py makemigrations clientes_pedidos
python manage.py migrate
```

## Beneficios
✅ **Integridad de Stock**: No se vende 2 veces el mismo repuesto
✅ **Trazabilidad**: Se sabe exactamente qué está reservado y por quién
✅ **Automatización**: Al facturar al contado, se reduce stock automáticamente
✅ **Flexibilidad**: Se pueden cancelar pedidos y liberar reservas
✅ **Reportes**: Se puede reportar stock disponible vs. reservado

## Flujo de Usuario
1. Vendedor crea pedido de venta de repuestos
2. Sistema valida stock disponible
3. Sistema crea reservas automáticamente
4. Stock aparece como "reservado" (no disponible para otros clientes)
5. Vendedor factura al contado
6. Sistema confirma venta y reduce stock real
7. Si se cancela: se libera la reserva
