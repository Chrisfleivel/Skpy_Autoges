from django.contrib import messages
from django.shortcuts import redirect, render

from configuraciones_maestras.models import ConfiguracionApariencia


def home_view(request):
    """
    Vista para la página de inicio después del login.
    """
    return render(request, 'home.html')

def configurar_apariencia(request):
    config, _ = ConfiguracionApariencia.objects.get_or_create(
        pk=1,
        defaults={
            'tema': ConfiguracionApariencia.THEME_DEFAULT,
            'tipografia': ConfiguracionApariencia.FONT_ROBOTO,
            'tamanio': 16,
        }
    )

    if request.method == 'POST':
        config.tema = request.POST.get('tema', ConfiguracionApariencia.THEME_DEFAULT)
        config.tipografia = request.POST.get('tipografia', ConfiguracionApariencia.FONT_ROBOTO)
        config.tamanio = int(request.POST.get('tamanio', 16))
        config.save()
        # messages.success(request, "Configuración de apariencia actualizada correctamente.")
        return redirect('configurar_apariencia')

    return render(request, 'proyecto_base/apariencia.html', {'config': config})