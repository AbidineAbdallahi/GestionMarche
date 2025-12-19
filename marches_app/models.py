# models.py
from django.db import models



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

class Marche(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    titre = models.CharField(max_length=500)
    autorite = models.CharField(max_length=255, blank=True, null=True)
    type_publication = models.CharField(max_length=255, blank=True, null=True)
    statut = models.CharField(max_length=255, blank=True, null=True)
    date_publication = models.DateField(blank=True, null=True)
    date_debut = models.DateField(blank=True, null=True)
    date_fin = models.DateField(blank=True, null=True)
    montant = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateField(blank=True, null=True)

class Document(models.Model):
    marche = models.ForeignKey(Marche, on_delete=models.CASCADE, related_name='documents')
    file_name = models.CharField(max_length=255)
    file_url = models.CharField(max_length=500, blank=True, null=True)
   
