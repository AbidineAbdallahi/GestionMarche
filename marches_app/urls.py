from django.urls import path
from . import views
from . import views1
from .views import login_view, logout_view
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path("", views.marche_list, name="marche_list"),
    path("marches/<str:marche_id>/", views.marche_detail, name="marche_detail"),
    path("marchesApi", views1.liste_marches, name="liste_marches"),
    path('marche/<int:marche_id>/', views1.marche_detail, name='marche_detail'),
    path("attributions/", views.attribution_list, name="attribution_list"),
    path("ppm/", views.ppm_list, name="ppm"),
    path('stats/', views.stats_entreprises, name='stats'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path("validator/", views.validator_list, name="validator_list"),
    path("validator/<str:marche_id>/", views.validator_detail, name="validator_detail"),
    path("validator/<str:marche_id>/action/", views.validator_action, name="validator_action"),
    path("collector", views.collector_dashboard, name="collector_dashboard"),
    path('ajouter-marche/', views.marche_create, name='marche_create'),
    path('logout/', views.logout_view, name='logout_view'),
    path("marches/<str:marche_id>/modifier/", views.marche_update, name="marche_update"),
    path("documents/<int:doc_id>/supprimer/", views.document_delete, name="document_delete"),
    path('visiteur/', views.visiteurs_view, name='visiteur'),
    path("register/", views.register_view, name="create_user"),
    path("entreprises/ajouter/", views.attributaire_create, name="attributaire_create"),
    path("docs/<str:marche_id>/<str:filename>", views.serve_document, name="serve_document"),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)