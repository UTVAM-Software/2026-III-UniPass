from django.db import models

class RegistroAcceso(models.Model):
    usuario = models.ForeignKey('cuentas.PerfilUsuario', on_delete=models.CASCADE, related_name='registros_acceso')
    fecha_hora = models.DateTimeField(auto_now_add=True)
    tipo_acceso = models.CharField(max_length=20)  # Entrada / Salida
    permitido = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.usuario} - {self.fecha_hora.strftime('%Y-%m-%d %H:%M')}"