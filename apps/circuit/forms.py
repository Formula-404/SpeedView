from django import forms
from .models import Circuit

class CircuitForm(forms.ModelForm):
    """
    Form yang dibuat secara otomatis dari model Circuit.
    """
    class Meta:
        model = Circuit
        fields = [
            'name',
            'map_image_url',
            'circuit_type',
            'direction',
            'location',
            'country',
            'last_used',
            'length_km',
            'turns',
            'grands_prix',
            'seasons',
            'grands_prix_held',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'e.g., Silverstone Circuit'}),
            'map_image_url': forms.URLInput(attrs={'class': 'input-field', 'placeholder': 'https://...'}),
            'location': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'e.g., Silverstone'}),
            'country': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'e.g., United Kingdom'}),
            'last_used': forms.NumberInput(attrs={'class': 'input-field', 'placeholder': 'e.g., 2023'}),
            'length_km': forms.NumberInput(attrs={'class': 'input-field', 'placeholder': 'e.g., 5.891'}),
            'turns': forms.NumberInput(attrs={'class': 'input-field', 'placeholder': 'e.g., 18'}),
            'grands_prix': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'e.g., British Grand Prix'}),
            'seasons': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'e.g., 1950–present'}),
            'grands_prix_held': forms.NumberInput(attrs={'class': 'input-field', 'placeholder': 'e.g., 58'}),
            'circuit_type': forms.Select(attrs={'class': 'input-field'}),
            'direction': forms.Select(attrs={'class': 'input-field'}),
        }

