from io import BytesIO
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from xhtml2pdf import pisa


def render_to_pdf_xhtml2pdf(template_src, context_dict):
    html = render_to_string(template_src, context_dict)
    result = BytesIO()
    pdf = pisa.CreatePDF(src=html, dest=result)
    if pdf.err:
        return None
    return result.getvalue()
