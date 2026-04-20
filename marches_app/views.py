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
import os
import uuid
import json
from django.db import transaction

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
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.groups.filter(name="Validator").exists():
                return redirect("marche_list")
            elif user.groups.filter(name="Collector").exists():
                return redirect("collector_dashboard")
            else:
                return redirect("marche_list")

    return render(request, "login.html")


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
            Q(titre__icontains=search) |
            Q(autorite__icontains=search)
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

    # 🔐 sécurité accès
    if not request.user.groups.filter(name__in=["Collector", "Validator", "Admin"]).exists():
        if marche.statut != "VALIDATED":
            return HttpResponseForbidden("Accès refusé")

    # ✅ booléens corrects
    is_validator = request.user.groups.filter(name="Validator").exists()
    is_collector = request.user.groups.filter(name="Collector").exists()

    return render(request, "marche_details.html", {
        "marche": marche,
        "documents": marche.documents.all(),
        "attributions": marche.attributions.select_related("attributaire"),
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

        if action in ["VALIDATED", "REJECTED"]:
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

    marches_list = Marche.objects.all().order_by("-date_publication")

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


@never_cache
@login_required
def marche_create(request):
    if not request.user.groups.filter(name="Collector").exists():
        return HttpResponseForbidden("Accès réservé au Collector")

    if request.method == "POST":
        form = MarcheForm(request.POST, request.FILES)

        if form.is_valid():
            with transaction.atomic():
                # 1. Enregistrer le marché dans la base
                marche = form.save(commit=False)
                marche.id = str(uuid.uuid4())
                marche.statut = "PENDING"
                marche.save()

                # 2. Créer le dossier du marché
                marche_folder = os.path.join(BASE_FOLDER, str(marche.id))
                os.makedirs(marche_folder, exist_ok=True)

                # 3. Récupérer tous les fichiers envoyés
                uploaded_files = request.FILES.getlist("files")

                documents_json = []

                for uploaded_file in uploaded_files:
                    if not uploaded_file:
                        continue

                    file_name = uploaded_file.name
                    file_path = os.path.join(marche_folder, file_name)

                    # Sauvegarde physique du fichier
                    with open(file_path, "wb+") as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)

                    # Sauvegarde en base
                    Document.objects.create(
                        marche=marche,
                        file_name=file_name,
                        file_url=file_path
                    )

                    documents_json.append({
                        "file_name": file_name,
                        "file_url": file_path
                    })

                # 4. Créer le fichier marche.json
                marche_data = {
                    "id": str(marche.id),
                    "titre": marche.titre,
                    "autorite": marche.autorite,
                    "type_publication": marche.type_publication,
                    "date_publication": marche.date_publication.isoformat() if marche.date_publication else None,
                    "date_debut": marche.date_debut.isoformat() if marche.date_debut else None,
                    "date_fin": marche.date_fin.isoformat() if marche.date_fin else None,
                    "montant": float(marche.montant) if marche.montant is not None else None,
                    "statut": marche.statut,
                    "documents": documents_json
                }

                json_path = os.path.join(marche_folder, "marche.json")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(marche_data, f, ensure_ascii=False, indent=4)

            return redirect("collector_dashboard")

    else:
        form = MarcheForm()

    return render(request, "marche_form.html", {"form": form})
def write_marche_json(marche):
    marche_folder = os.path.join(BASE_FOLDER, str(marche.id))
    os.makedirs(marche_folder, exist_ok=True)

    documents_json = []
    for doc in marche.documents.all():
        documents_json.append({
            "file_name": doc.file_name,
            "file_url": doc.file_url
        })

    marche_data = {
        "id": str(marche.id),
        "titre": marche.titre,
        "autorite": marche.autorite,
        "type_publication": marche.type_publication,
        "date_publication": marche.date_publication.isoformat() if marche.date_publication else None,
        "date_debut": marche.date_debut.isoformat() if marche.date_debut else None,
        "date_fin": marche.date_fin.isoformat() if marche.date_fin else None,
        "montant": float(marche.montant) if marche.montant is not None else None,
        "statut": marche.statut,
        "documents": documents_json
    }

    json_path = os.path.join(marche_folder, "marche.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(marche_data, f, ensure_ascii=False, indent=4)

@never_cache
@login_required
def marche_update(request, marche_id):
    marche = get_object_or_404(Marche, id=marche_id)

    if not request.user.groups.filter(name="Collector").exists():
        return HttpResponseForbidden("Accès réservé au Collector")

    if marche.statut != "PENDING":
        return HttpResponseForbidden("Impossible de modifier ce marché")

    if request.method == "POST":
        form = MarcheForm(request.POST, request.FILES, instance=marche)

        if form.is_valid():
            with transaction.atomic():
                old_statut = marche.statut
                marche = form.save(commit=False)
                marche.statut = old_statut
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