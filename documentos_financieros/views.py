from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic import ListView

from .forms import (
    AutofacturaForm,
    ComprobanteEgresoForm,
    DocumentoFinancieroForm,
    FacturaForm,
    ReciboDineroForm,
)
from .models import DocumentoFinanciero


class DocumentoListView(ListView):
    model = DocumentoFinanciero
    template_name = 'documentos_financieros/documento_list.html'
    context_object_name = 'documentos'
    paginate_by = 15

    def get_queryset(self):
        return DocumentoFinanciero.objects.select_related('cliente', 'proveedor', 'moneda').order_by('-fecha_emision')


def documento_crear(request, tipo='general'):
    form_map = {
        'general': DocumentoFinancieroForm,
        'factura': FacturaForm,
        'autofactura': AutofacturaForm,
        'recibo': ReciboDineroForm,
        'egreso': ComprobanteEgresoForm,
    }
    form_class = form_map.get(tipo, DocumentoFinancieroForm)
    titulo_map = {
        'general': 'documento financiero general',
        'factura': 'factura',
        'autofactura': 'autofactura',
        'recibo': 'recibo de dinero',
        'egreso': 'comprobante de egreso',
    }
    titulo = titulo_map.get(tipo, 'documento financiero')

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            if tipo == 'autofactura':
                instance.tipo_documento = 'autofactura'
            elif tipo == 'factura':
                instance.tipo_documento = 'factura_venta'
            elif tipo == 'recibo':
                instance.tipo_documento = 'recibo_dinero'
            elif tipo == 'egreso':
                instance.tipo_documento = 'comprobante_egreso'
            instance.save()
            messages.success(request, f'{titulo.capitalize()} registrada correctamente.')
            return redirect('documento_list')
    else:
        form = form_class()

    return render(
        request,
        'documentos_financieros/documento_form.html',
        {'form': form, 'titulo': titulo},
    )
