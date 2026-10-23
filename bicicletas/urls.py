from django.urls import path
from . import views

urlpatterns = [
    path('mis-bicicletas/', views.mis_bicicletas, name='mis_bicicletas'),
    path('registrar/', views.registrar_bicicleta, name='registrar_bicicleta'),
]