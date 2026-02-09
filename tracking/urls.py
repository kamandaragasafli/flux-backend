from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_external

from .views import (
    RegisterView,
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
    NotificationDeleteView,
    admin_dashboard_home,
    admin_dashboard_users,
    admin_dashboard_routes,
    admin_dashboard_locations,
    admin_dashboard_notifications,
    admin_dashboard_map,
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'schedules', VisitScheduleViewSet, basename='schedule')
router.register(r'visits', HospitalVisitViewSet, basename='visit')

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/user/", CurrentUserView.as_view(), name="current-user"),
    path("users/register/", RegisterView.as_view(), name="register-users"),  # Mobile app compatibility
    path("users/login/", LoginView.as_view(), name="login-users"),  # Mobile app compatibility
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
    path("notifications/<int:pk>/delete/", NotificationDeleteView.as_view(), name="notification-delete"),
    path("dashboard/", admin_dashboard_home, name="dashboard_home"),
    path("dashboard/users/", admin_dashboard_users, name="dashboard_users"),
    path("dashboard/routes/", admin_dashboard_routes, name="dashboard_routes"),
    path("dashboard/locations/", admin_dashboard_locations, name="dashboard_locations"),
    path("dashboard/notifications/", admin_dashboard_notifications, name="dashboard_notifications"),
    path("dashboard/map/", admin_dashboard_map, name="dashboard_map"),
    path("user-dashboard/", views.user_dashboard, name="user-dashboard"),
    # External data endpoints (Solvey Pharma)
    path("external/users/", views_external.external_users, name="external-users"),
    path("external/orders/", views_external.external_orders, name="external-orders"),
    path("external/doctors/", views_external.external_doctors, name="external-doctors"),
    path("external/regions-areas/", views_external.external_regions_areas, name="external-regions-areas"),
    path("external/hospitals/", views_external.external_hospitals, name="external-hospitals"),
    path("external/cities/", views_external.external_cities, name="external-cities"),
    path("external/tables/", views_external.external_tables, name="external-tables"),
    path("external/table-info/", views_external.external_table_info, name="external-table-info"),
    path("external/custom/", views_external.external_custom_data, name="external-custom"),
    # Solvey Database API Endpoints
    path("solvey/regions/", views.get_solvey_regions, name="solvey-regions"),
    path("solvey/cities/", views.get_solvey_cities, name="solvey-cities"),
    path("solvey/hospitals/", views.get_solvey_hospitals, name="solvey-hospitals"),
    path("solvey/doctors/", views.get_solvey_doctors, name="solvey-doctors"),
    # Location Permission Reports
    path("location-permission-reports/", views.create_location_permission_report, name="location-permission-reports"),
    # Visited Doctors
    path("visited-doctors/", views.add_visited_doctor, name="add-visited-doctor"),
    path("visited-doctors/list/", views.get_visited_doctors, name="get-visited-doctors"),
    # Medicines
    path("medicines/", views.get_medicines, name="get-medicines"),
    path("medicines/<int:medicine_id>/", views.get_medicine_detail, name="get-medicine-detail"),
    # ViewSet routes
    path("", include(router.urls)),
]


