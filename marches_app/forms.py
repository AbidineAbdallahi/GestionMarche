from django import forms
from .models import Marche

from django import forms
from .models import Attributaire


class AttributaireForm(forms.ModelForm):

    telephone = forms.CharField(required=False)

    class Meta:
        model = Attributaire

        fields = [
            "nom",
            "nif",
            "telephone",
            "email",
            "adresse"
        ]

        widgets = {
            "nom": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "nif": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "telephone": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control"
            }),

            "adresse": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),
        }
class MarcheForm(forms.ModelForm):

    TYPE_CHOICES = [
        ("Appel d'offre", "Appel d'offre"),
        ("Attribution provisoire", "Attribution provisoire"),
        ("Attribution définitive", "Attribution définitive"),
        ("Avis de manifestation d'intérêt", "Avis de manifestation d'intérêt"),
    ]

    MODE_SELECTION_CHOICES = [
        ("Appel Offres Ouvert National", "Appel Offres Ouvert National"),
        ("Appel Offres Ouvert International", "Appel Offres Ouvert International"),
        ("Consultation", "Consultation"),
        ("Entente directe", "Entente directe"),
    ]

    TYPE_MARCHE_CHOICES = [
        ("Fournitures", "Fournitures"),
        ("Travaux", "Travaux"),
        ("Services", "Services"),
        ("Prestations intellectuelles", "Prestations intellectuelles"),
    ]

    type_publication = forms.ChoiceField(
        choices=TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select-modern'})
    )

    mode_selection = forms.ChoiceField(
        choices=MODE_SELECTION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select-modern'})
    )

    type_marche = forms.ChoiceField(
        choices=TYPE_MARCHE_CHOICES,
        required=False,
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
            'mode_selection',
            'type_marche',
            'date_publication',
            'date_debut',
            'date_fin',
            'montant'
        ]

from django import forms
from django.contrib.auth.models import User


class UserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"placeholder": "Mot de passe"})
    )

    password2 = forms.CharField(
        label="Confirmer mot de passe",
        widget=forms.PasswordInput(attrs={"placeholder": "Confirmer mot de passe"})
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "Prénom"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Nom"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # username automatique avec email
        user.username = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user