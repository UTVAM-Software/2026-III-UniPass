"""Permisos de UniPass y los tres grupos que los agrupan.

El grupo no autoriza nada por sí solo: la vista pregunta por el permiso.
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

ADMINISTRADOR = "Admins"
GUARDIA = "Seguridad"
ALUMNO = "Alumnos"

# Grupos creados antes de unificar el nombre. Sus usuarios pasan al grupo nuevo.
NOMBRES_ANTERIORES = {
    "Administrador": ADMINISTRADOR,
    "Guardia": GUARDIA,
    "Alumno": ALUMNO,
}

GESTIONAR_USUARIOS = "cuentas.gestionar_usuarios"
EDITAR_PERFIL = "cuentas.editar_propio_perfil"
ADMINISTRAR_BICICLETAS = "bicicletas.administrar_bicicletas"
EDITAR_BICICLETA = "bicicletas.editar_propia_bicicleta"
VER_QR = "bicicletas.ver_codigo_qr"
ESCANEAR = "accesos.escanear_acceso"
VER_HISTORIAL = "accesos.ver_historial"

# (app, modelo, codename) para localizar el Permission sin ambigüedad.
PERMISOS_POR_GRUPO = {
    ADMINISTRADOR: [
        ("cuentas", "perfilusuario", "gestionar_usuarios"),
        ("cuentas", "perfilusuario", "editar_propio_perfil"),
        ("bicicletas", "bicicleta", "administrar_bicicletas"),
        ("bicicletas", "bicicleta", "ver_codigo_qr"),
        ("accesos", "registroacceso", "escanear_acceso"),
        ("accesos", "registroacceso", "ver_historial"),
    ],
    GUARDIA: [
        ("accesos", "registroacceso", "escanear_acceso"),
    ],
    ALUMNO: [
        ("bicicletas", "bicicleta", "editar_propia_bicicleta"),
        ("bicicletas", "bicicleta", "ver_codigo_qr"),
    ],
}


def sincronizar_grupos(sender=None, **kwargs):
    """Crea los grupos y les pone exactamente sus permisos. Es idempotente."""
    from django.contrib.auth.models import Group, Permission

    encontrados = {}
    for claves in PERMISOS_POR_GRUPO.values():
        for app, modelo, codename in claves:
            permiso = Permission.objects.filter(
                content_type__app_label=app,
                content_type__model=modelo,
                codename=codename,
            ).first()
            if permiso is None:
                return
            encontrados[(app, modelo, codename)] = permiso

    for viejo, nuevo in NOMBRES_ANTERIORES.items():
        anterior = Group.objects.filter(name=viejo).first()
        if anterior is None:
            continue
        destino, _ = Group.objects.get_or_create(name=nuevo)
        for usuario in list(anterior.user_set.all()):
            usuario.groups.add(destino)
        anterior.delete()

    for nombre, claves in PERMISOS_POR_GRUPO.items():
        grupo, _ = Group.objects.get_or_create(name=nombre)
        grupo.permissions.set([encontrados[clave] for clave in claves])


def perfil_de(user):
    if not getattr(user, "is_authenticated", False):
        return None
    from cuentas.models import PerfilUsuario

    return PerfilUsuario.objects.filter(user=user).first()


def es_solo_lectura(user):
    """El superusuario nunca queda en solo lectura. Un usuario en Admins con MODO_LECTURA actúa como auditor."""
    if not _sesion_valida(user) or getattr(user, "is_superuser", False):
        return False
    from cuentas.models import PerfilUsuario

    perfil = perfil_de(user)
    return perfil is not None and perfil.modo_acceso == PerfilUsuario.MODO_LECTURA


def respuesta_si_solo_lectura(request):
    """Conserva la sesión y niega la escritura. Leer sigue permitido por el permiso."""
    if not es_solo_lectura(getattr(request, "user", None)):
        return None
    messages.error(request, "Tu perfil está en solo lectura. No puedes modificar datos.")
    return inicio_para(request.user)


def bicicletas_de(user):
    """Quien administra ve todas. El alumno solo las suyas. El resto, ninguna."""
    from bicicletas.models import Bicicleta

    consulta = Bicicleta.objects.select_related("usuario__user").order_by("numero_folio")
    if user.has_perm(ADMINISTRAR_BICICLETAS):
        return consulta
    perfil = perfil_de(user)
    puede_ver_las_suyas = user.has_perm(EDITAR_BICICLETA) or user.has_perm(VER_QR)
    if perfil is None or not puede_ver_las_suyas:
        return consulta.none()
    return consulta.filter(usuario=perfil)


def inicio_para(user):
    if user.has_perm(GESTIONAR_USUARIOS):
        return redirect("mis_bicicletas")
    if user.has_perm(ESCANEAR):
        return redirect("verificar_acceso")
    return redirect("mis_bicicletas")


def _sesion_valida(user):
    return bool(getattr(user, "is_authenticated", False) and getattr(user, "is_active", False))


def _permiso_concedido(user, permiso):
    """True solo con una concesión explícita. Cualquier otro resultado es negación."""
    if not isinstance(permiso, str) or not permiso.strip():
        return False
    return user.has_perm(permiso) is True


def _confirmar(request, permisos, alguno):
    user = getattr(request, "user", None)
    if not _sesion_valida(user) or not permisos:
        return False
    concedidos = [_permiso_concedido(user, permiso) for permiso in permisos]
    if alguno:
        return any(concedidos)
    return all(concedidos)


def _denegar(request):
    """Cierra la sesión y manda al login. Negar es la única salida si no hubo concesión."""
    from django.contrib.auth import logout

    try:
        logout(request)
    except Exception:
        pass
    messages.error(request, "No se pudo confirmar tu acceso. Vuelve a iniciar sesión.")
    return redirect("login")


def _proteger(permisos, alguno):
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            try:
                permitido = _confirmar(request, permisos, alguno)
            except Exception:
                return _denegar(request)
            if not permitido:
                return _denegar(request)
            return vista(request, *args, **kwargs)

        return envoltura

    return decorador


def requiere(permiso):
    """Exige sesión vigente y ese permiso. Si falta, falla o no se puede leer, va al login."""
    return _proteger((permiso,), alguno=False)


def requiere_alguno(*permisos):
    """Exige sesión vigente y al menos un permiso. Si falta, falla o no se puede leer, va al login."""
    return _proteger(permisos, alguno=True)