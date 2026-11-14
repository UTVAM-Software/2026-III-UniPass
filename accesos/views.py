from datetime import timedelta
import re
import uuid

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from bicicletas.models import Bicicleta
from cuentas.permisos import ESCANEAR, VER_HISTORIAL, requiere

from .models import RegistroAcceso

_UUID_EXACTO = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_FOLIO_EXACTO = re.compile(r"^[A-Za-z0-9-]{1,50}$")


def _consulta():
    return Bicicleta.objects.select_related("usuario__user")


def _buscar_qr(valor):
    """Solo un UUID completo. Cualquier otro carácter se rechaza."""
    texto = (valor or "").strip()
    if not _UUID_EXACTO.fullmatch(texto):
        return None
    return _consulta().filter(qr_token=uuid.UUID(texto)).first()


def _buscar_folio(valor):
    """Solo letras, números y guion. El resto no se consulta."""
    texto = (valor or "").strip()
    if not _FOLIO_EXACTO.fullmatch(texto):
        return None, "El folio solo puede tener letras, números y guiones."
    return _consulta().filter(numero_folio__iexact=texto).first(), None


@requiere(VER_HISTORIAL)
def historial_accesos(request):
    q = (request.GET.get("q") or "").strip()
    registros = RegistroAcceso.objects.select_related(
        "bicicleta__usuario__user",
        "registrado_por",
    ).order_by("-fecha_hora")

    if q:
        registros = registros.filter(
            Q(bicicleta__numero_folio__icontains=q)
            | Q(bicicleta__usuario__matricula__icontains=q)
            | Q(bicicleta__usuario__user__first_name__icontains=q)
            | Q(bicicleta__usuario__user__last_name__icontains=q)
            | Q(bicicleta__usuario__user__username__icontains=q)
            | Q(tipo_acceso__icontains=q)
        )

    paginator = Paginator(registros, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "accesos/historial.html",
        {"registros": page_obj, "q": q},
    )


@requiere(ESCANEAR)
def verificar_acceso(request):
    bicicleta = None
    folio = ""

    if request.method == "POST":
        accion = request.POST.get("action") or ""
        if accion in ("registrar_entrada", "registrar_salida"):
            bicicleta = _buscar_qr(request.POST.get("qr_token"))
            if bicicleta is None:
                messages.error(request, "El código QR no corresponde a una bicicleta registrada.")
            else:
                _registrar_movimiento(request, bicicleta, accion)
            return redirect("verificar_acceso")

        if "folio" in request.POST:
            bicicleta, error = _buscar_folio(request.POST.get("folio"))
            if error:
                messages.error(request, error)
            elif bicicleta is None:
                messages.error(request, "No se encontró una bicicleta con ese folio.")
                folio = request.POST.get("folio").strip()
                if not _FOLIO_EXACTO.fullmatch(folio):
                    folio = ""
            else:
                folio = bicicleta.numero_folio
        else:
            bicicleta = _buscar_qr(request.POST.get("codigo"))
            if bicicleta is None:
                messages.error(request, "El código QR no es válido o no está registrado.")

    return render(
        request,
        "accesos/verificar.html",
        {"bicicleta": bicicleta, "folio": folio},
    )


def _registrar_movimiento(request, bicicleta, accion):
    ultimo = bicicleta.accesos.order_by("-fecha_hora").first()

    if ultimo and (timezone.now() - ultimo.fecha_hora) < timedelta(seconds=30):
        messages.warning(request, "Espera al menos 30 segundos antes de registrar otro movimiento para esta bicicleta.")
        return

    if accion == "registrar_entrada":
        if ultimo and ultimo.tipo_acceso == RegistroAcceso.ENTRADA:
            messages.error(request, "Esa bicicleta ya tiene una entrada abierta.")
            return
        tipo = RegistroAcceso.ENTRADA
    else:
        if ultimo is None or ultimo.tipo_acceso != RegistroAcceso.ENTRADA:
            messages.error(request, "No hay una entrada abierta para registrar la salida.")
            return
        tipo = RegistroAcceso.SALIDA

    RegistroAcceso.objects.create(
        bicicleta=bicicleta,
        tipo_acceso=tipo,
        registrado_por=request.user,
    )
    messages.success(request, f"{tipo.capitalize()} registrada.")