from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.conf import settings
import os

from .models import Marche, Attribution, Attributaire, PpmMarche


# ======================================================
# PPM LIST
# ======================================================

def ppm_list(request):
    ppms = PpmMarche.objects.all()
    return render(request, "ppm.html", {
        "ppms": ppms
    })


# ======================================================
# LISTE MARCHÉS
# ======================================================

def marche_list(request):
    search = request.GET.get("search", "").strip()
    statut = request.GET.get("statut", "").strip()
    type_pub = request.GET.get("type", "").strip()

    marches = Marche.objects.all()

    if search:
        marches = marches.filter(
            Q(titre__icontains=search) |
            Q(autorite__icontains=search) |
            Q(id__icontains=search)
        )

    if statut:
        marches = marches.filter(statut__iexact=statut)

    if type_pub:
        marches = marches.filter(type_publication__icontains=type_pub)

    paginator = Paginator(marches, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "marche_list.html", {
        "page_obj": page_obj,
        "marches": page_obj,
        "search": search,
        "statut": statut,
        "type_pub": type_pub,
    })


# ======================================================
# DÉTAIL MARCHÉ
# ======================================================

def marche_detail(request, marche_id):
    marche = get_object_or_404(Marche, id=marche_id)

    # 🔹 Attributions
    attributions = marche.attributions.select_related("attributaire").all()

    # 🔹 Documents depuis la base
    documents = marche.documents.all()

    return render(request, "marche_details.html", {
        "marche": marche,
        "documents": documents,
        "attributions": attributions
    })

# ======================================================
# LISTE ATTRIBUTIONS
# ======================================================

def attribution_list(request):
    search = request.GET.get('search', '').strip()
    marche_id = request.GET.get('marche', '').strip()

    attributions = Attribution.objects.select_related(
        'marche',
        'attributaire'
    )

    # 🔍 Recherche globale
    if search:
        attributions = attributions.filter(
            Q(marche__id__icontains=search) |
            Q(attributaire__nom__icontains=search) |
            Q(fichier_source__icontains=search)
        )

    # 🔎 Filtre par marché
    if marche_id:
        attributions = attributions.filter(
            marche__id__icontains=marche_id
        )

    attributions = attributions.order_by('-created_at')

    paginator = Paginator(attributions, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'attribution_list.html', {
        'attributions': page_obj,
        'page_obj': page_obj,
        'search': search,
        'marche_id': marche_id,
    })
def stats_entreprises(request):

    entreprises = (
        Attribution.objects
        .values('attributaire__nom')
        .annotate(
            nombre_marches=Count('marche', distinct=True),
            total_montant=Sum('montant')
        )
        .order_by('-nombre_marches')
    )

    paginator = Paginator(entreprises, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'stat.html', {
        'page_obj': page_obj,
        'entreprises': page_obj
    })