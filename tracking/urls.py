from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

from .views import (
    LoginView,
    StartRouteView,
    StopRouteView,
    PauseRouteView,
    ResumeRouteView,
    CreateLocationView,
    RouteDetailView,
    CurrentUserView,
    LastLocationsView,
    RoutesListView,
    VisitScheduleViewSet,
    HospitalVisitViewSet,
    NotificationListView,
    NotificationCreateView,
    NotificationMarkReadView,
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'schedules', VisitScheduleViewSet, basename='schedule')
router.register(r'visits', HospitalVisitViewSet, basename='visit')

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/user/", CurrentUserView.as_view(), name="current-user"),
    path("movqe-son-json/", LastLocationsView.as_view(), name="last-locations"),
    path("routes/", RoutesListView.as_view(), name="routes-list"),
    path("routes/start/", StartRouteView.as_view(), name="route-start"),
    path("routes/stop/", StopRouteView.as_view(), name="route-stop"),
    path("routes/pause/", PauseRouteView.as_view(), name="route-pause"),
    path("routes/resume/", ResumeRouteView.as_view(), name="route-resume"),
    path("locations/", CreateLocationView.as_view(), name="location-create"),
    path("routes/<int:pk>/", RouteDetailView.as_view(), name="route-detail"),
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/create/", NotificationCreateView.as_view(), name="notification-create"),
    path("notifications/<int:pk>/mark-read/", NotificationMarkReadView.as_view(), name="notification-mark-read"),
    path("dashboard/", views.admin_dashboard, name="dashboard"),
    # ViewSet routes
    path("", include(router.urls)),
]


