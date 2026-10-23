from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from bicicletas.models import Bicicleta  # Ajusta la importación según tu proyecto
from .models import RegistroAcceso        # Ajusta según tu modelo de historial de accesos

@login_required
def verificar_acceso(request):
    # Verificación de rol (Policía/Guardia/Admin)
    perfil = getattr(request.user, 'perfilusuario', None) or getattr(request.user, 'perfil', None)
    rol = getattr(perfil, 'rol', '').lower() if perfil else ''

    if rol not in ['policia', 'guardia', 'admin', 'administrativo']:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('mis_bicicletas')

    bicicleta = None
    if request.method == 'POST':
        query = request.POST.get('folio', '').strip()
        
        try:
            # CORRECCIÓN AQUÍ: Se usa numero_folio o qr_token según el campo del modelo
            bicicleta = Bicicleta.objects.filter(numero_folio=query).first() or \
                        Bicicleta.objects.filter(qr_token=query).first()
            
            if not bicicleta:
                messages.error(request, f'No se encontró ninguna bicicleta con el folio/código: {query}')
        except Exception as e:
            messages.error(request, f'Error al consultar el folio: {e}')

    return render(request, 'accesos/verificar.html', {'bicicleta': bicicleta})