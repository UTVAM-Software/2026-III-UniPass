from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from cuentas.models import UsuarioPerfil
from .forms import BicicletaForm
from .models import Bicicleta

@login_required
def registrar_bicicleta(request):
    if request.method == 'POST':
        form = BicicletaForm(request.POST)
        if form.is_valid():
            bicicleta = form.save(commit=False)
            
            # Obtiene o crea el perfil para el usuario actual en caso de que no exista
            perfil, _ = UsuarioPerfil.objects.get_or_create(user=request.user)
            
            bicicleta.usuario = perfil
            bicicleta.save()
            return redirect('mis_bicicletas')
    else:
        form = BicicletaForm()
    
    return render(request, 'bicicletas/registrar_bicicleta.html', {'form': form})


@login_required
def mis_bicicletas(request):
    perfil, _ = UsuarioPerfil.objects.get_or_create(user=request.user)
    bicicletas = Bicicleta.objects.filter(usuario=perfil)
    return render(request, 'bicicletas/mis_bicicletas.html', {'bicicletas': bicicletas})