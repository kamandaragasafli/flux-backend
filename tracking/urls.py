from django.urls import path
from . import views

from .views import (
    LoginView,
    StartRouteView,
    StopRouteView,
    CreateLocationView,
    RouteDetailView,
    CurrentUserView,
    LastLocationsView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/user/", CurrentUserView.as_view(), name="current-user"),
    path("movqe-son-json/", LastLocationsView.as_view(), name="last-locations"),
    path("routes/start/", StartRouteView.as_view(), name="route-start"),
    path("routes/stop/", StopRouteView.as_view(), name="route-stop"),
    path("locations/", CreateLocationView.as_view(), name="location-create"),
    path("routes/<int:pk>/", RouteDetailView.as_view(), name="route-detail"),
    path("dashboard/", views.admin_dashboard, name="dashboard"),
]


