from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
import os
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('linkzur_app.urls')),
]

# Only serve React build in production (DEBUG=False)
if not settings.DEBUG:
    urlpatterns += [re_path(r'^.*$', TemplateView.as_view(template_name='index.html'))]

# Serve media in dev
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG or os.environ.get("SERVE_MEDIA", "") == "1":
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

