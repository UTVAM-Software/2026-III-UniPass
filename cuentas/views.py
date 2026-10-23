from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

@login_required
def lista_usuarios(request):
    usuarios = User.objects.all()
    return render(request, 'cuentas/lista_usuarios.html', {'usuarios': usuarios})
# Create your views here.
