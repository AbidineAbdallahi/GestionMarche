from django.db import models
from django.conf import settings


class Attributaire(models.Model):
    nom = models.CharField(max_length=255)
    nif = models.CharField(max_length=100, blank=True, null=True, unique=True)
    telephone = models.JSONField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom


class Attribution(models.Model):

    marche = models.ForeignKey(
        'Marche',
        on_delete=models.CASCADE,
        related_name='attributions'
    )

    attributaire = models.ForeignKey(
        Attributaire,
        on_delete=models.CASCADE,
        related_name='attributions'
    )

    fichier_source = models.CharField(max_length=255)

    montant = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    devise = models.CharField(max_length=10, default="MRU")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("marche", "attributaire", "fichier_source")

    def __str__(self):
        return f"{self.marche.id} - {self.attributaire.nom}"


class PpmMarche(models.Model):
    reference_ppm = models.CharField(max_length=100)
    annee = models.PositiveSmallIntegerField(null=True, blank=True)
    autorite = models.TextField(null=True, blank=True)
    abreviation = models.CharField(max_length=50, null=True, blank=True)
    nombre_activites = models.IntegerField(null=True, blank=True)

    date_approbation = models.DateTimeField(null=True, blank=True)
    date_publication = models.DateTimeField(null=True, blank=True)
    statut_ppm = models.CharField(max_length=50, null=True, blank=True)
    nombre_revisions = models.IntegerField(null=True, blank=True)
    date_creation = models.DateTimeField(null=True, blank=True)
    date_update = models.DateTimeField(null=True, blank=True)

    numero_activite = models.IntegerField()
    realisation = models.TextField(null=True, blank=True)
    source_financement = models.CharField(max_length=100, null=True, blank=True)
    type_marche = models.CharField(max_length=50, null=True, blank=True)
    mode_selection = models.CharField(max_length=50, null=True, blank=True)

    date_lancement = models.DateTimeField(null=True, blank=True)
    date_attribution = models.DateTimeField(null=True, blank=True)
    date_demarrage = models.DateTimeField(null=True, blank=True)
    date_achevement = models.DateTimeField(null=True, blank=True)

    statut_activite = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "ppm_marche"
        unique_together = ("reference_ppm", "numero_activite")
        ordering = ["reference_ppm", "numero_activite"]

    def __str__(self):
        return f"{self.reference_ppm} - Activité {self.numero_activite}"


from django.db import models
from django.contrib.auth.models import User


class Marche(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    titre = models.CharField(max_length=500)
    autorite = models.CharField(max_length=255, blank=True, null=True)
    type_publication = models.CharField(max_length=255, blank=True, null=True)

    # nouveaux champs
    mode_selection = models.CharField(max_length=255, blank=True, null=True)
    type_marche = models.CharField(max_length=150, blank=True, null=True)

    # statut validation
    statut = models.CharField(
        max_length=20,
        default='PENDING'
    )

    date_publication = models.DateField(blank=True, null=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    montant = models.CharField(max_length=255, null=True, blank=True)
    updated_at = models.DateField(null=True, blank=True)

    # 🔥 propriétaire du marché (collector)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marches_created"
    )

    def __str__(self):
        return self.id


class Document(models.Model):
    marche = models.ForeignKey(Marche, on_delete=models.CASCADE, related_name='documents')
    file_name = models.CharField(max_length=255)
    file_url = models.CharField(max_length=500, blank=True, null=True)


# ======================================================
# 🔥 NOUVEAU MODEL : HISTORIQUE VALIDATION
# ======================================================

class MarcheValidation(models.Model):
    ACTION_CHOICES = [
        ('VALIDATED', 'Validated'),
        ('REJECTED', 'Rejected'),
    ]

    marche = models.ForeignKey(
        Marche,
        on_delete=models.CASCADE,
        related_name='validation_history'
    )

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    commentaire = models.TextField(blank=True, null=True)

    date_action = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.marche.id} - {self.action}"