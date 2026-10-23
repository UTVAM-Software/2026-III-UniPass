from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def iniciar_sesion(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            perfil = getattr(user, 'perfilusuario', None) or getattr(user, 'perfil', None)
            rol = getattr(perfil, 'rol', '').lower() if perfil else ''

            if rol in ['policia', 'guardia']:
                return redirect('verificar_acceso')
            elif rol in ['admin', 'administrativo']:
                return redirect('mis_bicicletas')
            else:
                return redirect('mis_bicicletas')
    else:
        form = AuthenticationForm()
        
    return render(request, 'cuentas/login.html', {'form': form})

def cerrar_sesion(request):
    logout(request)
    return redirect('login')

@login_required
def lista_usuarios(request):
    perfil = getattr(request.user, 'perfilusuario', None) or getattr(request.user, 'perfil', None)
    rol = getattr(perfil, 'rol', '').lower() if perfil else ''
    
    # Restricción de acceso solo para administradores (Mitigación OWASP A01)
    if rol not in ['admin', 'administrativo']:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('mis_bicicletas')

    # Obtener usuarios registrados
    usuarios = User.objects.all().order_by('-date_joined')
    return render(request, 'cuentas/lista_usuarios.html', {'usuarios': usuarios})