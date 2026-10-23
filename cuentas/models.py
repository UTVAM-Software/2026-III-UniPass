from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    ROLES = (
        ('alumno', 'Alumno'),
        ('policia', 'Policía / Seguridad'),
        ('admin', 'Administrativo / Sistemas'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    matricula = models.CharField(max_length=20, blank=True, null=True)
    rol = models.CharField(max_length=20, choices=ROLES, default='alumno')

    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"