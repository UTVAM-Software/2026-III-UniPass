from django.urls import path
from . import views

urlpatterns = [
    path('registrar/', views.registrar_bicicleta, name='registrar_bicicleta'),
    path('mis-bicicletas/', views.mis_bicicletas, name='mis_bicicletas'),
]