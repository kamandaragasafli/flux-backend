from django.contrib import admin
from django.urls import path, include
from tracking.views import admin_dashboard_home
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("dashboard/", admin_dashboard_home, name="admin_dashboard"),
    path("api/", include("tracking.urls")),
] 
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


