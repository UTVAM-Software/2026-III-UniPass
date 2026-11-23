import secrets

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cuentas.forms import EditarUsuarioForm, NuevoUsuarioForm, PerfilForm
from cuentas.models import PerfilUsuario
from cuentas.permisos import (
    ADMINISTRADOR,
    ALUMNO,
    EDITAR_PERFIL,
    GESTIONAR_USUARIOS,
    es_solo_lectura,
    inicio_para,
    perfil_de,
    requiere,
    respuesta_si_solo_lectura,
)


def _es_superusuario(user):
    return bool(getattr(user, "is_authenticated", False) and getattr(user, "is_superuser", False))


def _usuarios_para_perfil():
    usuarios = list(
        User.objects.filter(is_superuser=False)
        .prefetch_related("groups")
        .order_by("username")
    )
    perfiles = {
        perfil.user_id: perfil
        for perfil in PerfilUsuario.objects.filter(user__in=usuarios)
    }
    for usuario in usuarios:
        perfil = perfiles.get(usuario.id)
        grupos = list(usuario.groups.all())
        usuario.modo_actual = perfil.modo_acceso if perfil else PerfilUsuario.MODO_CLIENTE
        usuario.nombre_grupo = grupos[0].name if grupos else "Sin grupo"
    return usuarios


def iniciar_sesion(request):
    if request.user.is_authenticated and not _es_superusuario(request.user):
        return inicio_para(request.user)

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and not request.user.is_authenticated and form.is_valid():
        usuario = form.get_user()
        login(request, usuario)
        if not usuario.is_superuser:
            return inicio_para(usuario)
        return redirect("login")

    contexto = {"form": form, "usuarios_perfil": []}
    if _es_superusuario(request.user):
        contexto["usuarios_perfil"] = _usuarios_para_perfil()
    return render(request, "cuentas/login.html", contexto)


@require_POST
def asignar_perfiles(request):
    if not _es_superusuario(request.user):
        if getattr(request.user, "is_authenticated", False):
            messages.error(request, "Solo el superusuario puede asignar cliente o solo lectura.")
            return inicio_para(request.user)
        return redirect("login")

    modos = {PerfilUsuario.MODO_CLIENTE, PerfilUsuario.MODO_LECTURA}
    usuarios = User.objects.filter(is_superuser=False)
    with transaction.atomic():
        for usuario in usuarios:
            modo = request.POST.get(f"modo_{usuario.pk}")
            if modo not in modos:
                continue
            perfil, _ = PerfilUsuario.objects.get_or_create(user=usuario)
            if perfil.modo_acceso != modo:
                perfil.modo_acceso = modo
                perfil.save(update_fields=["modo_acceso"])
    messages.success(request, "Perfiles de cliente y solo lectura actualizados.")
    return redirect("login")


@require_POST
def cerrar_sesion(request):
    logout(request)
    return redirect("login")


@requiere(GESTIONAR_USUARIOS)
def lista_usuarios(request):
    usuarios = list(
        User.objects.exclude(is_superuser=True)
        .exclude(groups__name=ADMINISTRADOR)
        .prefetch_related("groups")
        .order_by("username")
    )
    perfiles = {
        perfil.user_id: perfil
        for perfil in PerfilUsuario.objects.filter(user__in=usuarios)
    }
    for usuario in usuarios:
        perfil = perfiles.get(usuario.id)
        grupos = list(usuario.groups.all())
        usuario.matricula_perfil = perfil.matricula if perfil and perfil.matricula else "—"
        usuario.nombre_grupo = grupos[0].name if grupos else "Sin grupo"
    return render(request, "cuentas/lista_usuarios.html", {"usuarios": usuarios})


@requiere(GESTIONAR_USUARIOS)
def nuevo_usuario(request):
    if request.method == "POST":
        bloqueo = respuesta_si_solo_lectura(request)
        if bloqueo:
            return bloqueo
    form = NuevoUsuarioForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        grupo = Group.objects.filter(name=form.cleaned_data["tipo"]).first()
        if grupo is None:
            messages.error(request, "El grupo de acceso no está configurado. Aplica las migraciones.")
            return redirect("nuevo_usuario")

        clave = secrets.token_urlsafe(9)
        with transaction.atomic():
            user = form.save(commit=False)
            user.set_password(clave)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            PerfilUsuario.objects.create(
                user=user,
                matricula=(form.cleaned_data.get("matricula") or "").strip() or None,
            )
            user.groups.set([grupo])
        messages.success(
            request,
            f"Cuenta {user.username} creada. Contraseña temporal: {clave}",
        )
        return redirect("lista_usuarios")

    return render(request, "cuentas/nuevo_usuario.html", {"form": form})


@requiere(GESTIONAR_USUARIOS)
def editar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk, is_superuser=False)
    if request.method == "POST":
        bloqueo = respuesta_si_solo_lectura(request)
        if bloqueo:
            return bloqueo

    perfil, _ = PerfilUsuario.objects.get_or_create(user=usuario)
    grupo_actual = usuario.groups.first()
    form = EditarUsuarioForm(
        request.POST or None,
        initial={
            "first_name": usuario.first_name,
            "last_name": usuario.last_name,
            "email": usuario.email,
            "matricula": perfil.matricula or "",
            "tipo": grupo_actual.name if grupo_actual else ALUMNO,
        },
    )
    if request.method == "POST" and form.is_valid():
        grupo = Group.objects.filter(name=form.cleaned_data["tipo"]).first()
        with transaction.atomic():
            usuario.first_name = form.cleaned_data["first_name"]
            usuario.last_name = form.cleaned_data["last_name"]
            usuario.email = form.cleaned_data["email"]
            usuario.save()
            perfil.matricula = (form.cleaned_data.get("matricula") or "").strip() or None
            perfil.save()
            if grupo:
                usuario.groups.set([grupo])
        messages.success(request, f"Datos de {usuario.username} actualizados correctamente.")
        return redirect("lista_usuarios")

    return render(
        request,
        "cuentas/editar_usuario.html",
        {"form": form, "usuario_editado": usuario},
    )


@require_POST
@requiere(GESTIONAR_USUARIOS)
def eliminar_usuario(request, pk):
    bloqueo = respuesta_si_solo_lectura(request)
    if bloqueo:
        return bloqueo
    usuario = get_object_or_404(User, pk=pk)
    if usuario != request.user:
        usuario.delete()
        messages.success(request, "Usuario eliminado correctamente.")
    return redirect("lista_usuarios")


@require_POST
@requiere(GESTIONAR_USUARIOS)
def restablecer_clave_usuario(request, pk):
    bloqueo = respuesta_si_solo_lectura(request)
    if bloqueo:
        return bloqueo
    usuario = get_object_or_404(User, pk=pk)
    clave_temporal = "UniPass2026!"
    usuario.set_password(clave_temporal)
    usuario.save()
    messages.success(
        request,
        f"Contraseña de {usuario.username} restablecida a: {clave_temporal}",
    )
    return redirect("lista_usuarios")


@requiere(EDITAR_PERFIL)
def editar_perfil(request):
    es_admin_activo = request.user.has_perm(GESTIONAR_USUARIOS) and not es_solo_lectura(request.user)

    if request.method == "POST":
        bloqueo = respuesta_si_solo_lectura(request)
        if bloqueo:
            return bloqueo
        if not es_admin_activo:
            messages.error(request, "Solo los administradores pueden modificar la información del perfil.")
            return redirect("editar_perfil")

    perfil = perfil_de(request.user)
    if perfil is None:
        perfil = PerfilUsuario.objects.create(user=request.user)

    form = PerfilForm(
        request.POST or None,
        user=request.user,
        puede_editar=es_admin_activo,
        puede_editar_matricula=es_admin_activo,
        initial={
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
            "matricula": perfil.matricula or "",
        },
    )
    if request.method == "POST" and form.is_valid():
        request.user.first_name = form.cleaned_data["first_name"]
        request.user.last_name = form.cleaned_data["last_name"]
        request.user.email = form.cleaned_data["email"]
        clave = form.cleaned_data["password1"]
        if clave:
            request.user.set_password(clave)
        request.user.save()
        perfil.matricula = (form.cleaned_data.get("matricula") or "").strip() or None
        perfil.save()
        if clave:
            login(request, request.user)
        messages.success(request, "Perfil actualizado.")
        return redirect("editar_perfil")

    return render(
        request,
        "cuentas/perfil.html",
        {"form": form, "puede_editar_perfil": es_admin_activo},
    )