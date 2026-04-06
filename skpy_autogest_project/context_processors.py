from configuraciones_maestras.models import ConfiguracionApariencia


def apariencia_settings(request):
    config = ConfiguracionApariencia.objects.first()
    if not config:
        config = ConfiguracionApariencia(
            tema=ConfiguracionApariencia.THEME_DEFAULT,
            tipografia=ConfiguracionApariencia.FONT_ROBOTO,
            tamanio=16,
        )

    # Determinar el estilo de la navbar basado en el tema
    navbar_styles = {
        ConfiguracionApariencia.THEME_DEFAULT: 'dark',
        ConfiguracionApariencia.THEME_DARK: 'dark',
        ConfiguracionApariencia.THEME_EMERALD: 'dark',
        ConfiguracionApariencia.THEME_SUNSET: 'dark',
        ConfiguracionApariencia.THEME_OCEAN: 'dark',
        ConfiguracionApariencia.THEME_LIGHT: 'light',
    }
    navbar_style = navbar_styles.get(config.tema, 'dark')

    return {
        'theme_class': config.tema,
        'font_family': config.tipografia,
        'base_size': f"{config.tamanio}px",
        'navbar_style': navbar_style,
    }
