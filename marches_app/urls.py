from django.urls import path
from . import views
from . import views1
urlpatterns = [
    path("", views.marche_list, name="marche_list"),
    path("marches/<str:marche_id>/", views.marche_detail, name="marche_detail"),
    path("marchesApi", views1.liste_marches, name="liste_marches"),
    path('marche/<int:marche_id>/', views1.marche_detail, name='marche_detail'),
    path("attributions/", views.attribution_list, name="attribution_list"),
    path("ppm/", views.ppm_list, name="ppm"),
    path('stats/', views.stats_entreprises, name='stats'),
]
