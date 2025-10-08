from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('linkzur_app.urls')),
]

# ✅ Serve static + media files (in dev only)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ✅ Add this LAST so it doesn’t override static
urlpatterns += [re_path(r'^.*$', TemplateView.as_view(template_name='index.html'))]
