
from datetime import timedelta

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from bicicletas.models import Bicicleta
from cuentas.models import PerfilUsuario
from cuentas.permisos import ESCANEAR, VER_HISTORIAL
from .models import RegistroAcceso


def _obtener_permiso(ruta_permiso):
    app_label, codename = ruta_permiso.split(".")
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


class AccesosFlujoTests(TestCase):
    def setUp(self):
        self.guardia = User.objects.create_user(username="guardia_test", password="Password123!")
        self.guardia.user_permissions.add(
            _obtener_permiso(ESCANEAR),
            _obtener_permiso(VER_HISTORIAL),
        )

        self.alumno_user = User.objects.create_user(
            username="2131100999", first_name="Ana", last_name="López", password="Password123!"
        )
        self.perfil, _ = PerfilUsuario.objects.get_or_create(
            user=self.alumno_user, defaults={"matricula": "2131100999"}
        )
        self.bici = Bicicleta.objects.create(
            usuario=self.perfil,
            numero_folio="F-999",
            marca="Trek",
            color="Negro",
        )

    def test_usuario_sin_permiso_no_accede_a_escaner(self):
        self.client.login(username="2131100999", password="Password123!")
        resp = self.client.get(reverse("verificar_acceso"))
        self.assertIn(resp.status_code, (302, 403))

    def test_entrada_salida_y_antirebote(self):
        self.client.login(username="guardia_test", password="Password123!")
        url = reverse("verificar_acceso")

        # 1. Registrar entrada válida
        self.client.post(url, {"action": "registrar_entrada", "qr_token": str(self.bici.qr_token)})
        self.assertEqual(RegistroAcceso.objects.count(), 1)
        self.assertEqual(RegistroAcceso.objects.first().tipo_acceso, RegistroAcceso.ENTRADA)

        # 2. Intentar registrar salida antes de 30s (debe bloquearse por anti-rebote)
        self.client.post(url, {"action": "registrar_salida", "qr_token": str(self.bici.qr_token)})
        self.assertEqual(RegistroAcceso.objects.count(), 1)

        # 3. Simular que pasaron 31 segundos y registrar salida
        reg = RegistroAcceso.objects.first()
        reg.fecha_hora = timezone.now() - timedelta(seconds=31)
        reg.save(update_fields=["fecha_hora"])

        self.client.post(url, {"action": "registrar_salida", "qr_token": str(self.bici.qr_token)})
        self.assertEqual(RegistroAcceso.objects.count(), 2)
        self.assertEqual(RegistroAcceso.objects.order_by("-fecha_hora").first().tipo_acceso, RegistroAcceso.SALIDA)
