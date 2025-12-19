from django.urls import path
from . import views

urlpatterns = [
    path("", views.marche_list, name="marche_list"),
    path("marches/<str:marche_id>/", views.marche_detail, name="marche_detail"),
    path("ppm/", views.ppm_list, name="ppm"),
]
