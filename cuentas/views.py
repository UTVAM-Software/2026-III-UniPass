import secrets

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cuentas.forms import NuevoUsuarioForm, PerfilForm
from cuentas.models import PerfilUsuario
from cuentas.permisos import (
    ADMINISTRADOR,
    EDITAR_PERFIL,
    GESTIONAR_USUARIOS,
    inicio_para,
    perfil_de,
    requiere,
)


def iniciar_sesion(request):
    if request.user.is_authenticated:
        return inicio_para(request.user)

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return inicio_para(form.get_user())

    return render(request, "cuentas/login.html", {"form": form})


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
@require_POST
@requiere(GESTIONAR_USUARIOS)
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if usuario != request.user:
        usuario.delete()
        messages.success(request, "Usuario eliminado correctamente.")
    return redirect("lista_usuarios")


@require_POST
@requiere(GESTIONAR_USUARIOS)
def restablecer_clave_usuario(request, pk):
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
    perfil = perfil_de(request.user)
    if perfil is None:
        perfil = PerfilUsuario.objects.create(user=request.user)

    puede_editar_matricula = request.user.has_perm(GESTIONAR_USUARIOS)
    form = PerfilForm(
        request.POST or None,
        user=request.user,
        puede_editar_matricula=puede_editar_matricula,
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
        if puede_editar_matricula:
            perfil.matricula = (form.cleaned_data.get("matricula") or "").strip() or None
            perfil.save()
        if clave:
            login(request, request.user)
        messages.success(request, "Perfil actualizado.")
        return redirect("editar_perfil")

    return render(request, "cuentas/perfil.html", {"form": form})
