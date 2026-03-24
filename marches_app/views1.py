import requests
from django.shortcuts import render

API_URL = "http://localhost:8085/api/v1/ao/list"
API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoiQURNSU4iLCJlbWFpbCI6ImFkbWluQHRlbnphay5jb20iLCJzdWIiOiJhZG1pbkB0ZW56YWsuY29tIiwiaWF0IjoxNzcyNDU5MTgwLCJleHAiOjE3NzI1NDU1ODB9.K9yii4wh6JM2oVb2kbjWoTfKudIAQS9HyKJ_DnFGH4U"
def liste_marches(request):
    # Page côté site
    page_number = int(request.GET.get("page", 0))  # page API commence à 0
    size_api = 10  # marchés par page

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json",
    }

    params = {
        "page": page_number,
        "size": size_api,
        "sort": "createAt,DESC"
    }

    marches = []
    total_pages = 1

    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        marches = data.get("content", [])
        total_elements = data.get("totalElements", len(marches))
        total_pages = data.get("totalPages", 1)
        print(len(marches))
        documents = marches[9]["documents"] if marches else []

        print("documents;;;;;;:",documents)
    except requests.exceptions.RequestException as e:
        print("Erreur API:", e)
        
    return render(request, "api.html", {
        "marches": marches,

        "page": page_number,
        "total_pages": total_pages,
    })
def marche_detail(request, marche_id):

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json",
    }

    page = 0
    size = 20
    marche = None

    try:
        while True:
            response = requests.get(
                API_URL,
                headers=headers,
                params={
                    "page": page,
                    "size": size,
                    "sort": "createAt,DESC"
                }
            )

            response.raise_for_status()
            data = response.json()

            marches = data.get("content", [])

            for m in marches:
                if str(m.get("id")) == str(marche_id):
                    marche = m
                    break

            if marche:
                break

            if page >= data.get("totalPages", 1) - 1:
                break

            page += 1

        if not marche:
            return render(request, "marche_detail.html", {
                "error": "Marché introuvable"
            })

        documents = marche.get("documents") or []

        # 🔥 Génération correcte des URLs locales
        for doc in documents:
            if not doc.get("urlFichier"):
                doc["urlFichier"] = f"http://localhost:8081/{marche_id}/{doc.get('titre')}"

        return render(request, "marche_detail.html", {
            "marche": marche,
            "documents": documents
        })

    except requests.exceptions.RequestException as e:
        return render(request, "marche_detail.html", {
            "error": f"Erreur API : {e}"
        })