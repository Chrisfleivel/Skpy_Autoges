

from django.shortcuts import render


def home_view(request):
    """
    Vista para la página de inicio después del login.
    """
    return render(request, 'home.html')