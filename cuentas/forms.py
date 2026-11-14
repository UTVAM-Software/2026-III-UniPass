from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from cuentas.permisos import ALUMNO, GUARDIA
from cuentas.validacion import clave_segura, correo_seguro, folio_seguro, texto_seguro, usuario_seguro


class NuevoUsuarioForm(forms.ModelForm):
    matricula = forms.CharField(
        label="Matrícula",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "pattern": "[A-Za-z0-9-]{1,20}", "maxlength": "20"}),
    )
    tipo = forms.ChoiceField(
        label="Grupo",
        choices=[(ALUMNO, "Alumnos"), (GUARDIA, "Seguridad")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        labels = {
            "username": "Usuario",
            "first_name": "Nombre(s)",
            "last_name": "Apellidos",
            "email": "Correo",
        }
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. 20261234", "pattern": "[A-Za-z0-9-]+", "maxlength": "150"}),
            "first_name": forms.TextInput(attrs={"class": "form-control", "pattern": "[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 \\-]+", "maxlength": "150"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "pattern": "[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 \\-]+", "maxlength": "150"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "maxlength": "254"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = False

    def clean_username(self):
        return usuario_seguro(self.cleaned_data.get("username"))

    def clean_first_name(self):
        return texto_seguro(self.cleaned_data.get("first_name"), vacio=True)

    def clean_last_name(self):
        return texto_seguro(self.cleaned_data.get("last_name"), vacio=True)

    def clean_email(self):
        return correo_seguro(self.cleaned_data.get("email"), vacio=True)

    def clean_matricula(self):
        valor = self.cleaned_data.get("matricula")
        if not (valor or "").strip():
            return ""
        return folio_seguro(valor, "La matrícula solo puede tener letras, números y guiones.")

    def clean(self):
        limpio = super().clean()
        if limpio.get("tipo") == ALUMNO and not (limpio.get("matricula") or "").strip():
            self.add_error("matricula", "La matrícula es obligatoria para un alumno.")
        return limpio


class PerfilForm(forms.Form):
    first_name = forms.CharField(label="Nombre(s)", max_length=150, disabled=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(label="Apellidos", max_length=150, required=False, disabled=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(label="Correo", required=False, disabled=True, widget=forms.EmailInput(attrs={"class": "form-control"}))
    matricula = forms.CharField(label="Matrícula", max_length=20, required=False, disabled=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    password1 = forms.CharField(label="Nueva contraseña", required=False, widget=forms.PasswordInput(attrs={"class": "form-control"}))
    password2 = forms.CharField(label="Confirmar contraseña", required=False, widget=forms.PasswordInput(attrs={"class": "form-control"}))

    def __init__(self, *args, user=None, puede_editar_matricula=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        for campo in ["first_name", "last_name", "email", "matricula"]:
            if campo in self.fields:
                self.fields[campo].disabled = True

    def clean_first_name(self):
        return texto_seguro(self.cleaned_data.get("first_name"))

    def clean_last_name(self):
        return texto_seguro(self.cleaned_data.get("last_name"), vacio=True)

    def clean_email(self):
        return correo_seguro(self.cleaned_data.get("email"), vacio=True)

    def clean_matricula(self):
        valor = self.cleaned_data.get("matricula")
        if not (valor or "").strip():
            return ""
        return folio_seguro(valor, "La matrícula solo puede tener letras, números y guiones.")

    def clean_password1(self):
        return clave_segura(self.cleaned_data.get("password1"), vacio=True)

    def clean(self):
        limpio = super().clean()
        clave = limpio.get("password1") or ""
        confirmacion = limpio.get("password2") or ""
        if confirmacion:
            try:
                clave_segura(confirmacion)
            except ValidationError as exc:
                self.add_error("password2", exc)
        if clave or confirmacion:
            if clave != confirmacion:
                self.add_error("password2", "Las contraseñas no coinciden.")
            else:
                try:
                    validate_password(clave, self.user)
                except ValidationError as exc:
                    self.add_error("password1", exc)
        return limpio
