from django import forms
from .models import Bicicleta

class BicicletaForm(forms.ModelForm):
    class Meta:
        model = Bicicleta
        fields = ['numero_folio', 'marca', 'color']
        widgets = {
            'numero_folio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. A-12345'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Trek, Benotto'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Rojo, Negro'}),
        }