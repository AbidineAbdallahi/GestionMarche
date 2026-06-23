from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.views.decorators.cache import never_cache
from functools import wraps
import re
from django.db.models import Q
import os
from .models import Attribution
from .forms import UserCreateForm
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserCreateForm
import uuid
import json
from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.http import HttpResponseForbidden
from .forms import AttributaireForm
from .models import Attributaire

from .models import (
    Marche, Attribution, Attributaire,
    PpmMarche, Document, MarcheValidation
)
from .forms import MarcheForm


# ======================================================
# 🔐 AUTHENTIFICATION
# ======================================================



@never_cache
def login_view(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name="Collector").exists():
            return redirect("collector_dashboard")

        if request.user.groups.filter(name="Validator").exists():
            return redirect("marche_list")

        return redirect("visiteur")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.groups.filter(name="Collector").exists():
                return redirect("collector_dashboard")

            if user.groups.filter(name="Validator").exists():
                return redirect("marche_list")

            return redirect("visiteur")

        return render(request, "login.html", {
            "error": "Nom d'utilisateur ou mot de passe incorrect"
        })

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")

@never_cache
def logout_view(request):
    logout(request)
    response = redirect("login")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


# ======================================================
# 📊 PPM
# ======================================================

@never_cache
@login_required
def ppm_list(request):
    ppms = PpmMarche.objects.all()
    return render(request, "ppm.html", {"ppms": ppms})


# ======================================================
# 📋 LISTE MARCHÉS
# ======================================================

@never_cache
@login_required
def marche_list(request):
    search = request.GET.get("search", "").strip()
    statut = request.GET.get("statut", "").strip()
    type_pub = request.GET.get("type", "").strip()

    user = request.user

    # 🔐 logique accès
    if user.groups.filter(name__in=["Collector", "Validator", "Admin"]).exists():
        marches = Marche.objects.all()
    else:
        marches = Marche.objects.filter(statut="VALIDATED")

    # 🔍 filtres
    if search:
        marches = marches.filter(
            Q(titre__istartswith=search) |
            Q(autorite__istartswith=search)
        )

    if statut:
        marches = marches.filter(statut__iexact=statut)

    if type_pub:
        marches = marches.filter(type_publication__icontains=type_pub)

    paginator = Paginator(marches.order_by("-id"), 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    is_validator = user.groups.filter(name="Validator").exists()

    return render(request, "marche_list.html", {
        "marches": page_obj,
        "page_obj": page_obj,
        "search": search,
        "statut": statut,
        "type_pub": type_pub,
        "is_validator": is_validator,
    })


# ======================================================
# 🔍 DÉTAIL MARCHÉ
# ======================================================

@never_cache
@login_required
def marche_detail(request, marche_id):
    marche = get_object_or_404(Marche, id=marche_id)

    if not request.user.groups.filter(name__in=["Collector", "Validator", "Admin"]).exists():
        if marche.statut != "VALIDATED":
            return HttpResponseForbidden("Accès refusé")

    is_validator = request.user.groups.filter(name="Validator").exists()
    is_collector = request.user.groups.filter(name="Collector").exists()

    attributions = Attribution.objects.filter(
        marche=marche
    ).select_related("attributaire")

    first_attribution = attributions.first()

    return render(request, "marche_details.html", {
        "marche": marche,
        "documents": marche.documents.all(),
        "attributions": attributions,
        "first_attribution": first_attribution,
        "is_validator": is_validator,
        "is_collector": is_collector,
    })



# ======================================================
# 📄 LISTE ATTRIBUTIONS
# ======================================================

@never_cache
@login_required
def attribution_list(request):
    search = request.GET.get("search", "").strip()

    attributions = Attribution.objects.select_related("marche", "attributaire")

    if search:
        attributions = attributions.filter(
            Q(marche__id__icontains=search) |
            Q(attributaire__nom__icontains=search)
        )

    paginator = Paginator(attributions.order_by("-created_at"), 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "attribution_list.html", {
        "attributions": page_obj,
        "page_obj": page_obj,
        "search": search,
    })


# ======================================================
# 📊 STATS ENTREPRISES
# ======================================================

@never_cache
@login_required
def stats_entreprises(request):
    entreprises = (
        Attribution.objects
        .values("attributaire__nom")
        .annotate(
            nombre_marches=Count("marche", distinct=True),
            total_montant=Sum("montant")
        )
        .order_by("-nombre_marches")
    )

    paginator = Paginator(entreprises, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "stat.html", {
        "entreprises": page_obj,
        "page_obj": page_obj
    })


# ======================================================
# 🔐 DECORATEUR VALIDATOR
# ======================================================

def validator_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.groups.filter(name="Validator").exists():
            return HttpResponseForbidden("Accès réservé au VALIDATOR")
        return view_func(request, *args, **kwargs)
    return wrapper


# ======================================================
# 📋 LISTE VALIDATOR
# ======================================================

@never_cache
@login_required
@validator_required
def validator_list(request):
    marches = Marche.objects.filter(statut="PENDING").order_by("-id")

    return render(request, "validator.html", {
        "marches": marches
    })


# ======================================================
# 🔍 DETAIL VALIDATOR
# ======================================================

@never_cache
@login_required
@validator_required
def validator_detail(request, marche_id):
    marche = get_object_or_404(Marche, id=marche_id)
    history = marche.validation_history.all().order_by("-date_action")

    return render(request, "validatDetail.html", {
        "marche": marche,
        "history": history
    })


# ======================================================
# ✅ ACTION VALIDATION
# ======================================================

@never_cache
@login_required
def validator_action(request, marche_id):

    if not request.user.groups.filter(name__in=["Validator", "Admin"]).exists():
        return HttpResponseForbidden("Accès refusé")

    marche = get_object_or_404(Marche, id=marche_id)

    if request.method == "POST":
        action = request.POST.get("action")
        commentaire = request.POST.get("commentaire")

        if action in ["VALIDATED", "REJECTED","INCOMPLETE"]:
            marche.statut = action
            marche.save()

            MarcheValidation.objects.create(
                marche=marche,
                utilisateur=request.user,
                action=action,
                commentaire=commentaire
            )

    return redirect("marche_list")


# ======================================================
# 📥 COLLECTOR DASHBOARD
# ======================================================

@never_cache
@login_required
def collector_dashboard(request):
    if not request.user.groups.filter(name="Collector").exists():
        return HttpResponseForbidden("Accès réservé au Collector")

    search = request.GET.get("search", "").strip()
    statut = request.GET.get("statut", "").strip()
    type_pub = request.GET.get("type", "").strip()

    # ✅ chaque collector voit seulement ses marchés
    marches_list = Marche.objects.filter(
        created_by=request.user
    ).order_by("-date_publication")

    if search:
        marches_list = marches_list.filter(
            Q(titre__icontains=search) |
            Q(autorite__icontains=search) |
            Q(id__icontains=search)
        )

    if statut:
        marches_list = marches_list.filter(statut=statut)

    if type_pub:
        marches_list = marches_list.filter(type_publication=type_pub)

    paginator = Paginator(marches_list, 10)
    page_number = request.GET.get("page")
    marches = paginator.get_page(page_number)

    return render(request, "collector_dashboard.html", {
        "marches": marches,
        "search": search,
        "statut": statut,
        "type_pub": type_pub,
    })

# ======================================================
# ➕ CREATE MARCHE
# ======================================================


from django.db import transaction




BASE_FOLDER = r"C:\Users\abidi\Desktop\ExtractionDonne\docs_marche"
from decimal import Decimal, InvalidOperation

@never_cache
@login_required
def marche_create(request):
    if not request.user.groups.filter(name="Collector").exists():
        return HttpResponseForbidden("Accès réservé au Collector")

    if request.method == "POST":
        form = MarcheForm(request.POST, request.FILES)

        if form.is_valid():
            with transaction.atomic():

                marche = form.save(commit=False)
                marche.id = str(uuid.uuid4())[:15]
                marche.statut = "PENDING"
                marche.created_by = request.user

                # sécuriser montant
                try:
                    if marche.montant:
                        marche.montant = Decimal(
                            str(marche.montant).replace(",", ".")
                        )
                    else:
                        marche.montant = None
                except (InvalidOperation, ValueError):
                    marche.montant = None

                marche.save()

                entreprise_nom = request.POST.get("entreprise_nom")
                entreprise_nif = request.POST.get("entreprise_nif") or None
                entreprise_telephone = request.POST.get("entreprise_telephone")
                entreprise_email = request.POST.get("entreprise_email") or None
                entreprise_adresse = request.POST.get("entreprise_adresse") or None

                attributaire = None

                if entreprise_nom:

                    entreprise_nom = entreprise_nom[:20]

                    if entreprise_nif:
                        attributaire, created = Attributaire.objects.get_or_create(
                            nif=entreprise_nif,
                            defaults={
                                "nom": entreprise_nom,
                                "telephone": [entreprise_telephone] if entreprise_telephone else [],
                                "email": entreprise_email,
                                "adresse": entreprise_adresse,
                            }
                        )
                    else:
                        attributaire = Attributaire.objects.create(
                            nom=entreprise_nom,
                            nif=None,
                            telephone=[entreprise_telephone] if entreprise_telephone else [],
                            email=entreprise_email,
                            adresse=entreprise_adresse,
                        )

                    Attribution.objects.create(
                        marche=marche,
                        attributaire=attributaire,
                        fichier_source="Formulaire manuel",
                        montant=marche.montant,
                        devise="MRU"
                    )

                marche_folder = os.path.join(BASE_FOLDER, str(marche.id))
                os.makedirs(marche_folder, exist_ok=True)

                uploaded_files = request.FILES.getlist("files")
                documents_json = []

                for uploaded_file in uploaded_files:

                    if not uploaded_file:
                        continue

                    file_name = uploaded_file.name
                    file_path = os.path.join(marche_folder, file_name)

                    with open(file_path, "wb+") as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)

                    Document.objects.create(
                        marche=marche,
                        file_name=file_name,
                        file_url=file_path
                    )

                    documents_json.append({
                        "file_name": file_name,
                        "file_url": file_path
                    })

                marche_data = {
                    "id": str(marche.id),
                    "titre": marche.titre,
                    "autorite": marche.autorite,
                    "type_publication": marche.type_publication,
                    "date_publication": marche.date_publication.isoformat() if marche.date_publication else None,
                    "date_debut": marche.date_debut.isoformat() if marche.date_debut else None,
                    "date_fin": marche.date_fin.isoformat() if marche.date_fin else None,
                    "montant": float(marche.montant) if marche.montant else None,
                    "statut": marche.statut,
                    "documents": documents_json,
                    "entreprise": {
                        "nom": attributaire.nom if attributaire else None,
                        "nif": attributaire.nif if attributaire else None,
                        "telephone": attributaire.telephone if attributaire else [],
                        "email": attributaire.email if attributaire else None,
                        "adresse": attributaire.adresse if attributaire else None,
                    }
                }

                json_path = os.path.join(marche_folder, "marche.json")

                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(marche_data, f, ensure_ascii=False, indent=4)

            return redirect("collector_dashboard")

    else:
        form = MarcheForm()

    return render(request, "marche_form.html", {"form": form})

@never_cache
@login_required
def marche_update(request, marche_id):
    marche = get_object_or_404(Marche, id=marche_id)

    if not request.user.groups.filter(name="Collector").exists():
        return HttpResponseForbidden("Accès réservé au Collector")

    if marche.created_by != request.user:
        return HttpResponseForbidden(
            "Vous ne pouvez modifier que les marchés que vous avez créés."
        )

    if marche.statut not in ["PENDING", "INCOMPLETE"]:
        return HttpResponseForbidden("Impossible de modifier ce marché")

    last_validation = MarcheValidation.objects.filter(
        marche=marche
    ).order_by("-date_action").first()

    if request.method == "POST":
        form = MarcheForm(request.POST, request.FILES, instance=marche)

        if form.is_valid():
            with transaction.atomic():
                old_statut = marche.statut
                old_created_by = marche.created_by

                marche = form.save(commit=False)
                if old_statut == "INCOMPLETE":
                    marche.statut = "PENDING"
                else :
                    marche.statut = old_statut
                marche.created_by = old_created_by
                marche.save()

                marche_folder = os.path.join(BASE_FOLDER, str(marche.id))
                os.makedirs(marche_folder, exist_ok=True)

                uploaded_files = request.FILES.getlist("documents")

                for uploaded_file in uploaded_files:
                    if not uploaded_file:
                        continue

                    file_name = uploaded_file.name
                    file_path = os.path.join(marche_folder, file_name)

                    with open(file_path, "wb+") as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)

                    Document.objects.create(
                        marche=marche,
                        file_name=file_name,
                        file_url=file_path
                    )

                write_marche_json(marche)

            return redirect("marche_detail", marche_id=marche.id)

    else:
        form = MarcheForm(instance=marche)

    return render(request, "marche_update_form.html", {
        "form": form,
        "marche": marche,
        "documents": marche.documents.all(),
        "last_validation": last_validation,
    })

@never_cache
@login_required
def document_delete(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)

    if not request.user.groups.filter(name="Collector").exists():
        return HttpResponseForbidden("Accès réservé au Collector")

    if doc.marche.statut != "PENDING":
        return HttpResponseForbidden("Impossible de modifier")

    marche_id = doc.marche.id

    if request.method == "POST":
        # 🔥 pas de fichier physique à supprimer
        doc.delete()

    return redirect("marche_update", marche_id=marche_id)
from django.shortcuts import render
from .models import Marche

from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Marche

@never_cache
@login_required
def visiteurs_view(request):
    # afficher seulement les marchés validés
    marches_list = Marche.objects.filter(
        statut='VALIDATED'
    ).order_by('-date_publication', '-updated_at')

    # pagination
    paginator = Paginator(marches_list, 10)
    page = request.GET.get('page')
    marches = paginator.get_page(page)

    return render(request, 'visiteurs.html', {
        'marches': marches
    })
    # views.py




def register_view(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Compte créé avec succès.")
            return redirect("login")

    else:
        form = UserCreateForm()

    return render(request, "register.html", {
        "form": form
    })
@never_cache
@login_required
def attributaire_create(request):

    if not request.user.groups.filter(name="Collector").exists():
        return HttpResponseForbidden("Accès réservé au Collector")

    if request.method == "POST":

        nom = request.POST.get("nom")
        nif = request.POST.get("nif") or None
        telephone = request.POST.get("telephone")
        email = request.POST.get("email") or None
        adresse = request.POST.get("adresse") or None

        if nif:
            attributaire, created = Attributaire.objects.get_or_create(
                nif=nif,
                defaults={
                    "nom": nom,
                    "telephone": [telephone] if telephone else [],
                    "email": email,
                    "adresse": adresse,
                }
            )

            if not created:
                attributaire.nom = nom
                attributaire.telephone = [telephone] if telephone else []
                attributaire.email = email
                attributaire.adresse = adresse
                attributaire.save()

        else:
            Attributaire.objects.create(
                nom=nom,
                nif=None,
                telephone=[telephone] if telephone else [],
                email=email,
                adresse=adresse,
            )

        return redirect("collector_dashboard")

    form = AttributaireForm()

    return render(request, "attributaire_form.html", {
        "form": form
    })