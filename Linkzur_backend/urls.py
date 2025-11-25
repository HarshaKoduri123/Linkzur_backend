from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve
from linkzur_app.views_admin import approve_seller, reject_seller   # create this file


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('linkzur_app.urls')),
    # custom admin actions
    path("admin/approve-seller/<int:pending_id>/", approve_seller, name="approve_seller"),
    path("admin/reject-seller/<int:pending_id>/", reject_seller, name="reject_seller"),

]

# ✅ Serve media in production when DEBUG=False
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# ✅ Serve static+media in local development only
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


urlpatterns += [
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),
]
