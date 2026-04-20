from django import forms
from .models import Marche


class MarcheForm(forms.ModelForm):

    TYPE_CHOICES = [
        ("Appel d'offre", "Appel d'offre"),
        ("Attribution provisoire", "Attribution provisoire"),
        ("Attribution définitive", "Attribution définitive"),
        ("Avis de manifestation d'intérêt", "Avis de manifestation d'intérêt"),
    ]

    type_publication = forms.ChoiceField(
        choices=TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select-modern'})
    )

    date_publication = forms.DateField(
        required=False,
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    date_debut = forms.DateField(
        required=False,
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    date_fin = forms.DateField(
        required=False,
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Marche
        fields = [
            'titre',
            'autorite',
            'type_publication',
            'date_publication',
            'date_debut',
            'date_fin',
            'montant'
        ]