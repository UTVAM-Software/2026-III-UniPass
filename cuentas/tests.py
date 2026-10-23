from django.urls import path
from . import views

urlpatterns = [
    # ... tus otras rutas (login, logout, etc.)
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
]