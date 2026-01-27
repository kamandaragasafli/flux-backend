from django.contrib import admin
from django.urls import path, include
from tracking.views import admin_dashboard_home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("dashboard/", admin_dashboard_home, name="admin_dashboard"),
    path("api/", include("tracking.urls")),
]


