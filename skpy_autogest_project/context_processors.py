from configuraciones_maestras.models import ConfiguracionApariencia


def apariencia_settings(request):
    config = ConfiguracionApariencia.objects.first()
    if not config:
        config = ConfiguracionApariencia(
            tema=ConfiguracionApariencia.THEME_DEFAULT,
            tipografia=ConfiguracionApariencia.FONT_ROBOTO,
            tamanio=16,
        )

    theme_class = config.tema
    if request.user.is_authenticated:
        perfil = getattr(request.user, 'perfil', None)
        if perfil and getattr(perfil, 'tema', None):
            theme_class = perfil.tema

    # Determinar el estilo de la navbar basado en el tema
    navbar_styles = {
        ConfiguracionApariencia.THEME_DEFAULT: 'dark',
        ConfiguracionApariencia.THEME_DARK: 'dark',
        ConfiguracionApariencia.THEME_EMERALD: 'dark',
        ConfiguracionApariencia.THEME_SUNSET: 'dark',
        ConfiguracionApariencia.THEME_OCEAN: 'dark',
        ConfiguracionApariencia.THEME_LIGHT: 'light',
        'theme-default': 'dark',
        'theme-dark': 'dark',
        'theme-emerald': 'dark',
        'theme-sunset': 'dark',
        'theme-ocean': 'dark',
        'theme-light': 'light',
    }
    navbar_style = navbar_styles.get(theme_class, 'dark')

    return {
        'theme_class': theme_class,
        'font_family': config.tipografia,
        'base_size': f"{config.tamanio}px",
        'navbar_style': navbar_style,
    }
