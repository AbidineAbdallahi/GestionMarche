from django.shortcuts import render, get_object_or_404
from .models import Marche, Document
from django.shortcuts import render
from django.db.models import Q
from .models import Marche

from django.core.paginator import Paginator

from .models import PpmMarche


def ppm_list(request):
    ppms = PpmMarche.objects.all()
    return render(request, "ppm.html", {
        "ppms": ppms
    })

def marche_list(request):
    search = request.GET.get("search", "").strip()
    statut = request.GET.get("statut", "").strip()
    type_pub = request.GET.get("type", "").strip()

    marches = Marche.objects.all()

    if search:
        marches = marches.filter(
            Q(titre__icontains=search) |
            Q(autorite__icontains=search)
        )

    if statut:
        marches = marches.filter(statut__iexact=statut)

    if type_pub:
        marches = marches.filter(type_publication__icontains=type_pub)

    # ------------------------------
    #  PAGINATION
    # ------------------------------
    paginator = Paginator(marches, 10)  # 10 éléments par page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "marches": page_obj,     # Pour ton tableau
        "search": search,
        "statut": statut,
        "type_pub": type_pub,
    }

    return render(request, "marche_list.html", context)


def marche_detail(request, marche_id):
    marche = get_object_or_404(Marche, id=marche_id)
    documents = marche.documents.all()
    return render(request, 'marche_details.html', {
        'marche': marche,
        'documents': documents
    })