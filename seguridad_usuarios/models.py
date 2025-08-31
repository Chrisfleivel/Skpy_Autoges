# seguridad_usuarios/models.py

from django.db import models
from django.contrib.auth.models import User

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número de Teléfono")

    def __str__(self):
        return f'Perfil de {self.user.username}'