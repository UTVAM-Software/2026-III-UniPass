from django.shortcuts import render
from django.db.models import Q
from bicicletas.models import Bicicleta

def verificar_acceso(request):
    resultado = None
    bicicleta = None
    folio_buscado = ""

    if request.method == "POST":
        folio_buscado = request.POST.get("folio", "").strip()
        if folio_buscado:
            # Buscamos por numero_folio o por qr_token
            bicicletas = Bicicleta.objects.filter(
                Q(numero_folio__iexact=folio_buscado) | Q(qr_token__iexact=folio_buscado)
            )
            
            if bicicletas.exists():
                bicicleta = bicicletas.first()
                resultado = "permitido"
            else:
                resultado = "denegado"

    return render(request, "accesos/verificar.html", {
        "resultado": resultado,
        "bicicleta": bicicleta,
        "folio_buscado": folio_buscado,
    })