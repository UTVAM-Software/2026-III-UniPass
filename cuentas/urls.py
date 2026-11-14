from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.iniciar_sesion, name="login"),
    path("logout/", views.cerrar_sesion, name="logout"),
    path("perfil/", views.editar_perfil, name="editar_perfil"),
    path("usuarios/", views.lista_usuarios, name="lista_usuarios"),
    path("usuarios/nuevo/", views.nuevo_usuario, name="nuevo_usuario"),
    path("usuarios/<int:pk>/eliminar/", views.eliminar_usuario, name="eliminar_usuario"),
    path("usuarios/<int:pk>/restablecer/", views.restablecer_clave_usuario, name="restablecer_clave_usuario"),
]
