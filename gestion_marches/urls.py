from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('marches_app.urls')),  # inclut toutes les URLs de marches_app
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)