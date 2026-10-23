import uuid
from django.db import models

class Bicicleta(models.Model):
    usuario = models.ForeignKey('cuentas.PerfilUsuario', on_delete=models.CASCADE, related_name='bicicletas')
    numero_folio = models.CharField(max_length=50, unique=True)
    marca = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    qr_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f"{self.marca} ({self.numero_folio})"