from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

        # URLs publiques (autorisé sans login)
        self.public_urls = [
            '/login/',
            '/logout/',
            '/marchesApi',
        ]

    def __call__(self, request):

        path = request.path

        # autoriser fichiers static/media
        if path.startswith('/static') or path.startswith('/media'):
            return self.get_response(request)

        # autoriser URLs publiques
        if path in self.public_urls:
            return self.get_response(request)

        # 🔐 vérifier login
        if not request.user.is_authenticated:
            return redirect(reverse('login'))

        return self.get_response(request)