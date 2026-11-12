# configuraciones_maestras/forms.py

from django import forms
from django.core.exceptions import ValidationError
import re

from core.models import Moneda as MonedaFacade, TasaCambio as TasaCambioFacade
from .models import Proveedor, ContactoProveedor, AgenteTransporte, DespachanteAduana, Despachante, TasaCambio, Departamento, Cargo, Moneda, Empresa, Banco, OrdenPagoExterior, Sucursal
from cobranzas.models import Caja as CajaOperativa, AperturaCaja as AperturaCajaOperativa, CierreCaja as CierreCajaOperativa


class CajaForm(forms.ModelForm):
    """Formulario del maestro de cajas operativas de una sucursal.

    La sucursal no se edita acá: se fija desde la URL al guardar.
    El estado, saldos y empleados los maneja la operación de cobranzas.
    """

    class Meta:
        model = CajaOperativa
        fields = ['nombre', 'tipo', 'observaciones']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Caja 1'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones de la caja'}),
        }

    def __init__(self, *args, sucursal=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.sucursal = sucursal

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if self.sucursal:
            qs = CajaOperativa.objects.filter(sucursal=self.sucursal, nombre__iexact=nombre)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Ya existe una caja con ese nombre en la sucursal.')
        return nombre


class AperturaCajaOperativaForm(forms.ModelForm):
    """Apertura de una caja operativa de una sucursal desde el maestro de Cajas."""

    class Meta:
        model = AperturaCajaOperativa
        fields = ['monto_inicial', 'observaciones']
        widgets = {
            'monto_inicial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Ej. 500000'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones de la apertura'}),
        }


class CierreCajaOperativaForm(forms.ModelForm):
    """Cierre con arqueo de una caja operativa desde el maestro de Cajas."""

    class Meta:
        model = CierreCajaOperativa
        fields = ['monto_real', 'observaciones']
        widgets = {
            'monto_real': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Monto contado en caja'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones del cierre'}),
        }


class SucursalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        empresa_activa = Empresa.get_empresa_activa()
        if empresa_activa is None:
            self.fields['empresa'].queryset = Empresa.objects.none()
            self.fields['empresa'].widget = forms.HiddenInput()
        else:
            self.fields['empresa'].queryset = Empresa.objects.filter(pk=empresa_activa.pk)
            self.fields['empresa'].initial = empresa_activa.pk
            self.fields['empresa'].widget = forms.HiddenInput()

    class Meta:
        model = Sucursal
        fields = ['empresa', 'nombre', 'direccion', 'telefono', 'email', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la sucursal'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección de la sucursal'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono de la sucursal'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'direccion', 'telefono', 'email', 'ruc', 'timbrado', 'logo', 'sucursales']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la empresa'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección fiscal o principal'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono principal'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 80012345-6'}),
            'timbrado': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 12345678'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'sucursales': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 6}),
        }


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = [
            'tipo_persona',
            'razon_social',
            'nombre',
            'apellidos',
            'documento_identidad',
            'ruc',
            'direccion',
            'telefono',
            'email',
            'contacto',
            'estado',
        ]
        widgets = {
            'tipo_persona': forms.Select(attrs={'class': 'form-select'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Hyundai Motor Company'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Juan'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Pérez'}),
            'documento_identidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula o pasaporte'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 80012345-6'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección en Corea del Sur o Paraguay'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. +595981234567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej. contacto@proveedor.com'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contacto principal'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_persona = cleaned_data.get('tipo_persona')
        nombre = cleaned_data.get('nombre')
        razon_social = cleaned_data.get('razon_social')
        documento_identidad = cleaned_data.get('documento_identidad')
        ruc = cleaned_data.get('ruc')

        if tipo_persona == 'FISICA':
            if not nombre:
                self.add_error('nombre', 'El nombre es obligatorio para persona física.')
            if not documento_identidad:
                self.add_error('documento_identidad', 'El documento de identidad es obligatorio para persona física.')
            cleaned_data['razon_social'] = None
        elif tipo_persona == 'JURIDICA':
            if not razon_social:
                self.add_error('razon_social', 'La razón social es obligatoria para persona jurídica.')
            if not ruc:
                self.add_error('ruc', 'El RUC es obligatorio para persona jurídica.')
            cleaned_data['nombre'] = None
            cleaned_data['apellidos'] = None

        if ruc:
            digits = re.sub(r'\D', '', ruc)
            if len(digits) not in (10, 11, 13):
                self.add_error('ruc', 'El RUC debe contener entre 10 y 13 dígitos numéricos.')
            cleaned_data['ruc'] = digits

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in self.Meta.widgets:
                if isinstance(field.widget, forms.CheckboxInput):
                    continue
                field.widget.attrs.update({'class': 'form-control'})

class ContactoProveedorForm(forms.ModelForm):
    class Meta:
        model = ContactoProveedor
        fields = ['tipo_persona', 'nombre', 'apellidos', 'cargo', 'telefono', 'email']
        widgets = {
            'tipo_persona': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del contacto'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos del contacto'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cargo'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': field.widget.attrs.get('class', '') + ' form-control'})

class AgenteTransporteForm(forms.ModelForm):
    class Meta:
        model = AgenteTransporte
        fields = [
            'tipo_persona',
            'razon_social',
            'nombre',
            'apellidos',
            'documento_identidad',
            'ruc',
            'contacto',
            'telefono',
            'email',
            'direccion',
            'pais_operacion',
            'registro_autoridad',
            'tipo_servicio',
            'lugar_operacion',
            'tipo_carga_especialidad',
            'contacto_emergencia',
            'numero_poliza_seguro',
            'placa_vehiculo',
            'cedula_verde',
            'nombre_chofer',
            'cedula_chofer',
            'estado',
        ]
        widgets = {
            'tipo_persona': forms.Select(attrs={'class': 'form-select'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Busan Freight Co.'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Juan'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Pérez'}),
            'documento_identidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pasaporte o documento'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'BRN en Corea o RUC en Paraguay'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Persona de Contacto'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. +595981234567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej. contacto@agencia.com'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección de operación'}),
            'pais_operacion': forms.Select(attrs={'class': 'form-control'}),
            'registro_autoridad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. FIATA12345 o DINATRAN56789'}),
            'tipo_servicio': forms.Select(attrs={'class': 'form-control'}),
            'lugar_operacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Busan (BSN) / Incheon (ICN)'}),
            'tipo_carga_especialidad': forms.Select(attrs={'class': 'form-control'}),
            'contacto_emergencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contacto de Emergencia'}),
            'numero_poliza_seguro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de Póliza de Seguro'}),
            'placa_vehiculo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Chapa del camión / cigüeña'}),
            'cedula_verde': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula verde del vehículo'}),
            'nombre_chofer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del chofer'}),
            'cedula_chofer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula de Identidad del chofer'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DespachanteAduanaForm(forms.ModelForm):
    class Meta:
        model = DespachanteAduana
        fields = ['nombre', 'apellidos', 'razon_social', 'contacto', 'telefono', 'email', 'registro']

class DespachanteForm(forms.ModelForm):
    class Meta:
        model = Despachante
        fields = [
            'nombre_razon_social',
            'pais_codigo',
            'ruc_o_brn',
            'tipo_representacion',
            'sistema_gestion',
            'fecha_vencimiento_mandato',
            'contacto_email',
            'es_activo',
        ]
        widgets = {
            'nombre_razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Despachante XYZ S.A.'}),
            'pais_codigo': forms.Select(attrs={'class': 'form-control'}),
            'ruc_o_brn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 80012345-6 o BRN'}),
            'tipo_representacion': forms.Select(attrs={'class': 'form-control'}),
            'sistema_gestion': forms.Select(attrs={'class': 'form-control'}),
            'fecha_vencimiento_mandato': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contacto_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej. contacto@despachante.com'}),
            'es_activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in ('es_activo',):
                if not isinstance(field.widget, (forms.Select, forms.DateInput)):
                    field.widget.attrs.update({'class': field.widget.attrs.get('class', '') + ' form-control'})

class TasaCambioForm(forms.ModelForm):
    class Meta:
        model = TasaCambio
        fields = ['moneda_origen', 'moneda_destino', 'valor', 'fecha']
        widgets = {
            'moneda_origen': forms.Select(attrs={'class': 'form-control'}),
            'moneda_destino': forms.Select(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 6850.50', 'step': '0.0001'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        MonedaFacade.ensure_defaults()
        moneda_choices = [(codigo, nombre) for codigo, nombre in MonedaFacade.get_choices()]
        self.fields['moneda_origen'].choices = [('', 'Seleccione moneda')] + moneda_choices
        self.fields['moneda_destino'].choices = [('', 'Seleccione moneda')] + moneda_choices


class BancoForm(forms.ModelForm):
    class Meta:
        model = Banco
        fields = ['codigo', 'nombre', 'pais_codigo', 'direccion', 'swift', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. BCBP'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del banco'}),
            'pais_codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PY, KR, US'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'swift': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SWIFT/BIC'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class OrdenPagoExteriorForm(forms.ModelForm):
    class Meta:
        model = OrdenPagoExterior
        fields = [
            'tipo_documento_remitente',
            'numero_documento_remitente',
            'remitente_nombre',
            'remitente_direccion',
            'remitente_telefono',
            'forma_pago',
            'numero_cuenta',
            'moneda',
            'importe_orden',
            'comision_orden',
            'total_orden',
            'referencia_op',
            'numero_lote',
            'fecha_operacion',
            'banco_corresponsal',
            'ordenante',
            'banco_beneficiario',
            'pais_beneficiario',
            'cuenta_beneficiaria',
            'beneficiario',
            'motivo_transferencia',
            'concepto',
            'cotizacion',
            'estado',
            'observaciones',
        ]
        widgets = {
            'tipo_documento_remitente': forms.Select(attrs={'class': 'form-select'}),
            'numero_documento_remitente': forms.TextInput(attrs={'class': 'form-control'}),
            'remitente_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'remitente_direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'remitente_telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'forma_pago': forms.Select(attrs={'class': 'form-select'}),
            'numero_cuenta': forms.TextInput(attrs={'class': 'form-control'}),
            'moneda': forms.Select(attrs={'class': 'form-select'}),
            'importe_orden': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'comision_orden': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_orden': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'referencia_op': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_lote': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_operacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'banco_corresponsal': forms.Select(attrs={'class': 'form-select'}),
            'ordenante': forms.TextInput(attrs={'class': 'form-control'}),
            'banco_beneficiario': forms.Select(attrs={'class': 'form-select'}),
            'pais_beneficiario': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PY, KR, US'}),
            'cuenta_beneficiaria': forms.TextInput(attrs={'class': 'form-control'}),
            'beneficiario': forms.TextInput(attrs={'class': 'form-control'}),
            'motivo_transferencia': forms.TextInput(attrs={'class': 'form-control'}),
            'concepto': forms.TextInput(attrs={'class': 'form-control'}),
            'cotizacion': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        MonedaFacade.ensure_defaults()
        moneda_choices = [(codigo, f"{codigo} - {nombre}") for codigo, nombre in MonedaFacade.get_choices()]
        self.fields['moneda'].choices = [('', 'Seleccione moneda')] + moneda_choices
        for field in self.fields.values():
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        importe = cleaned_data.get('importe_orden') or 0
        comision = cleaned_data.get('comision_orden') or 0
        total = cleaned_data.get('total_orden') or 0
        if total and float(total) != float(importe) + float(comision):
            self.add_error('total_orden', 'El total debe ser igual a importe + comisión.')
        return cleaned_data

class DepartamentoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        empresa_activa = Empresa.get_empresa_activa()
        if empresa_activa is None:
            self.fields['empresa'].queryset = Empresa.objects.none()
            self.fields['empresa'].widget = forms.HiddenInput()
        else:
            self.fields['empresa'].queryset = Empresa.objects.filter(pk=empresa_activa.pk)
            self.fields['empresa'].initial = empresa_activa.pk
            self.fields['empresa'].widget = forms.HiddenInput()
        for field in self.fields.values():
            if field is self.fields.get('empresa'):
                continue
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Departamento
        fields = ['empresa', 'nombre', 'descripcion']

class CargoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Cargo
        fields = ['nombre', 'departamento', 'descripcion', 'vacantes', 'salario', 'roles']
        widgets = {
            'departamento': forms.Select(attrs={'class': 'form-control'}),
            'roles': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 6}),
        }

class MonedaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        MonedaFacade.ensure_defaults()
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '')
        if codigo:
            codigo = codigo.strip().upper()
            if len(codigo) != 3:
                raise ValidationError('El código debe tener exactamente 3 caracteres.')
        return codigo

    class Meta:
        model = Moneda
        fields = ['codigo', 'nombre']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. USD', 'maxlength': '3'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Dólar Estadounidense'}),
        }


