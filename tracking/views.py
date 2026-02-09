from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db.models import Max, Count, Q
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from datetime import timedelta
import requests
import os
import logging

from .models import (
    Route,
    LocationPoint,
    VisitSchedule,
    HospitalVisit,
    UserProfile,
    Notification,
    VisitedDoctor,
    LocationPermissionReport,
    Medicine,
)
from .models_solvey import SolveyRegion, SolveyCity, SolveyHospital, SolveyDoctor, SolveyMedicine
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    RouteSerializer,
    StartRouteSerializer,
    StopRouteSerializer,
    CreateLocationSerializer,
    VisitScheduleSerializer,
    HospitalVisitSerializer,
    UserProfileSerializer,
    NotificationSerializer,
    MedicineSerializer,
)

# SSL uyarılarını bastır (development için)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Logger təyin et
logger = logging.getLogger(__name__)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
                "token": str(refresh.access_token),
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class StartRouteView(generics.CreateAPIView):
    serializer_class = StartRouteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data={})
        serializer.is_valid(raise_exception=True)
        route = serializer.save()
        return Response(RouteSerializer(route).data, status=status.HTTP_201_CREATED)


class StopRouteView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = StopRouteSerializer(data={}, context={"request": request})
        serializer.is_valid(raise_exception=True)
        route = serializer.save()
        return Response(RouteSerializer(route).data, status=status.HTTP_200_OK)


class PauseRouteView(APIView):
    """Aktif route'u duraklatır (Doktor odasında)"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        route = Route.objects.filter(user=user, end_time__isnull=True).order_by('-start_time').first()
        
        if not route:
            return Response(
                {"detail": "Aktif route bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if route.is_paused:
            return Response(
                {"detail": "Route zaten duraklatılmış."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        route.is_paused = True
        route.paused_at = timezone.now()
        route.save(update_fields=['is_paused', 'paused_at'])
        
        return Response({
            "message": "Route duraklatıldı.",
            "route_id": route.id,
            "paused_at": route.paused_at
        })


class ResumeRouteView(APIView):
    """Duraklatılmış route'u devam ettirir"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        route = Route.objects.filter(user=user, end_time__isnull=True).order_by('-start_time').first()
        
        if not route:
            return Response(
                {"detail": "Aktif route bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not route.is_paused:
            return Response(
                {"detail": "Route duraklatılmamış."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Duraklatma süresini hesapla
        if route.paused_at:
            pause_duration = (timezone.now() - route.paused_at).total_seconds()
            route.total_paused_duration += int(pause_duration)
        
        route.is_paused = False
        route.paused_at = None
        route.save(update_fields=['is_paused', 'paused_at', 'total_paused_duration'])
        
        return Response({
            "message": "Route devam ettiriliyor.",
            "route_id": route.id,
            "total_paused_duration": route.total_paused_duration
        })


class CreateLocationView(generics.CreateAPIView):
    serializer_class = CreateLocationSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class RouteDetailView(generics.RetrieveAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [permissions.AllowAny]  # Dashboard için
    
    def get_queryset(self):
        # Staff user ise tüm route'ları görebilir
        if self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser):
            return Route.objects.all()
        # Normal user sadece kendi route'larını görebilir
        elif self.request.user.is_authenticated:
            return Route.objects.filter(user=self.request.user)
        # Unauthenticated ise boş döndür (dashboard'da staff kontrolü yapılır)
        return Route.objects.none()


class CurrentUserView(APIView):
    """Mevcut kullanıcının bilgilerini döndürür ve günceller"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # Profil bilgilerini al veya oluştur
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "profile": {
                "regions": profile.regions,
                "cities": profile.cities,
                "has_completed_profile": len(profile.regions) > 0 and len(profile.cities) > 0
            }
        })

    def patch(self, request):
        """Kullanıcı bilgilerini günceller"""
        user = request.user
        data = request.data

        # Kullanıcı bilgileri
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']

        # Profil bilgileri
        profile, created = UserProfile.objects.get_or_create(user=user)
        if 'regions' in data:
            regions = data['regions']
            if len(regions) > 3:
                return Response(
                    {"detail": "Maksimum 3 bölge seçebilirsiniz."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            profile.regions = regions
        if 'cities' in data:
            cities = data['cities']
            if len(cities) > 3:
                return Response(
                    {"detail": "Maksimum 3 şehir seçebilirsiniz."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            profile.cities = cities

        try:
            user.save()
            profile.save()
            return Response({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile": {
                    "regions": profile.regions,
                    "cities": profile.cities,
                    "has_completed_profile": len(profile.regions) > 0 and len(profile.cities) > 0
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RoutesListView(generics.ListAPIView):
    """Kullanıcının tüm route'larını listeler"""
    serializer_class = RouteSerializer
    # Dashboard için tüm route'ları görebilmek için AllowAny
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user_id = self.request.query_params.get('user')
        if user_id:
            # Belirli bir kullanıcının route'ları
            return Route.objects.filter(user_id=user_id).order_by('-start_time')
        elif self.request.user.is_authenticated:
            # Kendi route'ları
            return Route.objects.filter(user=self.request.user).order_by('-start_time')
        else:
            # Authenticated değilse boş döndür
            return Route.objects.none()


class LastLocationsView(APIView):
    """Tüm kullanıcıların son konumlarını döndürür (harita için)"""
    # Dashboard için session authentication kullanılır
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Session authentication ile gelen istekler için kontrol
        # Eğer authenticated değilse ve staff user değilse boş döndür
        if not request.user.is_authenticated:
            return Response({
                "features": [],
                "error": "Bu endpoint'e sadece admin kullanıcılar erişebilir."
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({
                "features": [],
                "error": "Bu endpoint'e sadece admin kullanıcılar erişebilir."
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Her kullanıcının son konumunu al
        users = User.objects.all()
        features = []
        
        for user in users:
            # Kullanıcının en son location point'ini al
            last_location = LocationPoint.objects.filter(
                route__user=user
            ).order_by('-timestamp').first()
            
            if last_location:
                route = last_location.route
                features.append({
                    "id": user.id,
                    "ad": user.username,
                    "username": user.username,  # Dashboard için
                    "lat": float(last_location.latitude),
                    "lng": float(last_location.longitude),
                    "status": route.connection_status if route else "unknown",
                    "is_paused": route.is_paused if route else False,
                })
        
        return Response({
            "features": features
        })


class NotificationListView(generics.ListAPIView):
    """Kullanıcının bildirimlerini listele"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class NotificationCreateView(APIView):
    """Dashboard'dan kullanıcıya bildirim gönder (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        user_id = request.data.get('user_id')
        notification_type = request.data.get('notification_type', 'message')
        title = request.data.get('title')
        message = request.data.get('message')
        
        if not user_id or not title or not message:
            return Response(
                {"detail": "user_id, title və message lazımdır."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "İstifadəçi tapılmadı."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message
        )
        
        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_201_CREATED
        )


class NotificationMarkReadView(APIView):
    """Bildirimi okundu olarak işaretle"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            return Response({"message": "Bildirim oxundu olaraq işarələndi."})
        except Notification.DoesNotExist:
            return Response(
                {"detail": "Bildirim tapılmadı."},
                status=status.HTTP_404_NOT_FOUND
            )


class NotificationDeleteView(APIView):
    """Bildirimi sil (Admin veya bildirim sahibi)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk)
            # Admin ise herhangi bir bildirimi silebilir, normal kullanıcı sadece kendi bildirimlerini
            if request.user.is_staff or request.user.is_superuser or notification.user == request.user:
                notification.delete()
                return Response({"message": "Bildirim silindi."}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"detail": "Bu bildirimi silməyə icazəniz yoxdur."},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Notification.DoesNotExist:
            return Response(
                {"detail": "Bildirim tapılmadı."},
                status=status.HTTP_404_NOT_FOUND
            )


def is_staff_user(user):
    return user.is_staff or user.is_superuser


@user_passes_test(is_staff_user)
def admin_dashboard_home(request):
    """Admin dashboard - ana səhifə"""
    
    total_users = User.objects.count()
    active_users = User.objects.filter(routes__end_time__isnull=True).distinct().count()
    total_routes = Route.objects.count()
    active_routes = Route.objects.filter(end_time__isnull=True).count()
    total_locations = LocationPoint.objects.count()
    total_hospital_visits = HospitalVisit.objects.count()
    total_visited_doctors = VisitedDoctor.objects.count()
    total_schedules = VisitSchedule.objects.count()
    total_location_reports = LocationPermissionReport.objects.count()
    
    last_24h = timezone.now() - timedelta(hours=24)
    routes_last_24h = Route.objects.filter(start_time__gte=last_24h).count()
    locations_last_24h = LocationPoint.objects.filter(timestamp__gte=last_24h).count()
    hospital_visits_last_24h = HospitalVisit.objects.filter(visit_date__gte=last_24h.date()).count()
    location_reports_last_24h = LocationPermissionReport.objects.filter(timestamp__gte=last_24h).count()

    active_routes_list = (
        Route.objects.filter(end_time__isnull=True)
        .select_related("user")
        .prefetch_related("points")
        .order_by("-start_time")[:20]
    )

    recent_location_reports = (
        LocationPermissionReport.objects.select_related("user")
        .order_by("-timestamp")[:50]
    )

    context = {
        "active_page": "home",
        "total_users": total_users,
        "active_users": active_users,
        "total_routes": total_routes,
        "active_routes": active_routes,
        "total_locations": total_locations,
        "routes_last_24h": routes_last_24h,
        "locations_last_24h": locations_last_24h,
        "hospital_visits_last_24h": hospital_visits_last_24h,
        "location_reports_last_24h": location_reports_last_24h,
        "active_routes_list": active_routes_list,
        "recent_location_reports": recent_location_reports,
        "total_hospital_visits": total_hospital_visits,
        "total_visited_doctors": total_visited_doctors,
        "total_schedules": total_schedules,
        "total_location_reports": total_location_reports,
    }
    return render(request, "dashboard_home.html", context)


@user_passes_test(is_staff_user)
def admin_dashboard_users(request):
    """Admin dashboard - istifadəçilər"""

    users = (
        User.objects.annotate(
            route_count=Count("routes"),
            location_count=Count("routes__points"),
            last_activity=Max("routes__start_time"),
            has_active_route=Count("routes", filter=Q(routes__end_time__isnull=True)),
        )
        .order_by("-date_joined")[:100]
    )
    context = {
        "active_page": "users",
        "users": users,
        "total_users": users.count(),
    }
    return render(request, "dashboard_users.html", context)


@user_passes_test(is_staff_user)
def admin_dashboard_routes(request):
    """Admin dashboard - route və xəstəxana ziyarətləri"""

    active_routes = Route.objects.filter(end_time__isnull=True).count()
    active_routes_list = (
        Route.objects.filter(end_time__isnull=True)
        .select_related("user")
        .prefetch_related("points")
        .order_by("-start_time")[:50]
    )
    recent_hospital_visits = (
        HospitalVisit.objects.select_related("user")
        .order_by("-visit_date", "-check_in_time")[:50]
    )

    context = {
        "active_page": "routes",
        "active_routes": active_routes,
        "active_routes_list": active_routes_list,
        "recent_hospital_visits": recent_hospital_visits,
    }
    return render(request, "dashboard_routes.html", context)


@user_passes_test(is_staff_user)
def admin_dashboard_locations(request):
    """Admin dashboard - konum nöqtələri"""

    last_24h = timezone.now() - timedelta(hours=24)
    locations_last_24h = LocationPoint.objects.filter(timestamp__gte=last_24h).count()
    recent_locations = (
        LocationPoint.objects.select_related("route__user")
        .order_by("-timestamp")[:100]
    )
    context = {
        "active_page": "locations",
        "locations_last_24h": locations_last_24h,
        "recent_locations": recent_locations,
    }
    return render(request, "dashboard_locations.html", context)


@user_passes_test(is_staff_user)
def admin_dashboard_notifications(request):
    """Admin dashboard - bildirişlər"""

    recent_notifications = (
        Notification.objects.select_related("user")
        .order_by("-created_at")[:100]
    )
    context = {
        "active_page": "notifications",
        "recent_notifications": recent_notifications,
    }
    return render(request, "dashboard_notifications.html", context)


@user_passes_test(is_staff_user)
def admin_dashboard_map(request):
    """Admin dashboard - xəritə"""
    context = {
        "active_page": "map",
    }
    return render(request, "dashboard_map.html", context)


class VisitScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing visit schedules
    - List all schedules for the authenticated user
    - Create new schedule
    - Update existing schedule
    - Delete schedule
    """
    serializer_class = VisitScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Her kullanıcı sadece kendi planlarını görebilir
        return VisitSchedule.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save()
    
    def perform_update(self, serializer):
        serializer.save()


class HospitalVisitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing hospital visits
    - List all visits for the authenticated user
    - Create new visit
    - Update existing visit
    - Delete visit
    """
    serializer_class = HospitalVisitSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Her kullanıcı sadece kendi ziyaretlerini görebilir
        return HospitalVisit.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save()


# ============================================================================
# Solvey Database API Endpoints
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_solvey_regions(request):
    """
    Solvey database-dən bütün bölgələri çəkir
    GET /api/solvey/regions/
    """
    try:
        regions = SolveyRegion.objects.using('external').all().order_by('region_name')
        data = [
            {
                'id': r.id,
                'name': r.region_name,
                'type': r.region_type
            }
            for r in regions
        ]
        return Response({'success': True, 'data': data})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_solvey_cities(request):
    """
    Solvey database-dən şəhərləri çəkir
    GET /api/solvey/cities/?region_id=X (opsional)
    """
    try:
        cities = SolveyCity.objects.using('external').all()
        
        # Region filter (opsional)
        region_id = request.GET.get('region_id')
        if region_id:
            try:
                region_id = int(region_id)
                cities = cities.filter(region_id=region_id)
            except ValueError:
                return Response({'success': False, 'error': 'Invalid region_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        cities = cities.order_by('city_name')
        data = [
            {
                'id': c.id,
                'name': c.city_name,
                'region_id': c.region_id
            }
            for c in cities
        ]
        return Response({'success': True, 'data': data})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_solvey_hospitals(request):
    """
    Solvey database-dən xəstəxanaları çəkir
    GET /api/solvey/hospitals/?city_id=X&region_id=X (opsional)
    """
    try:
        hospitals = SolveyHospital.objects.using('external').all()
        
        # City filter (opsional)
        city_id = request.GET.get('city_id')
        if city_id:
            try:
                city_id = int(city_id)
                hospitals = hospitals.filter(city_id=city_id)
            except ValueError:
                return Response({'success': False, 'error': 'Invalid city_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Region filter (opsional)
        region_id = request.GET.get('region_id')
        if region_id:
            try:
                region_id = int(region_id)
                hospitals = hospitals.filter(region_net_id=region_id)
            except ValueError:
                return Response({'success': False, 'error': 'Invalid region_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        hospitals = hospitals.order_by('hospital_name')
        data = [
            {
                'id': h.id,
                'name': h.hospital_name,
                'city_id': h.city_id,
                'region_id': h.region_net_id
            }
            for h in hospitals
        ]
        return Response({'success': True, 'data': data})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_solvey_doctors(request):
    """
    Solvey database-dən həkimləri çəkir
    GET /api/solvey/doctors/?region_id=X&city_id=X&hospital_id=X (opsional)
    """
    try:
        logger.info("[SOLVEY_DOCTORS] Starting get_solvey_doctors")
        # External database-dən həkimləri çək
        doctors = SolveyDoctor.objects.using('external').all()
        logger.info(f"[SOLVEY_DOCTORS] Initial doctors count: {doctors.count()}")
        
        # Region filter (opsional)
        region_id = request.GET.get('region_id')
        if region_id:
            try:
                region_id = int(region_id)
                logger.info(f"[SOLVEY_DOCTORS] Filtering by region_id={region_id}")
                doctors_before = doctors.count()
                doctors = doctors.filter(bolge_id=region_id)
                doctors_after = doctors.count()
                logger.info(f"[SOLVEY_DOCTORS] Before filter: {doctors_before}, After filter: {doctors_after}")
                
                # Əgər həkim tapılmadısa, bəlkə bölgə ID-si yanlışdır
                if doctors_after == 0:
                    logger.warning(f"[SOLVEY_DOCTORS] No doctors found for region_id={region_id}")
                    # Bölgədə həkim olub-olmadığını yoxla
                    try:
                        region = SolveyRegion.objects.using('external').filter(id=region_id).first()
                        if region:
                            logger.info(f"[SOLVEY_DOCTORS] Region exists: {region.region_name} (ID: {region.id})")
                        else:
                            logger.warning(f"[SOLVEY_DOCTORS] Region with ID {region_id} does not exist in database")
                    except Exception as e:
                        logger.error(f"[SOLVEY_DOCTORS] Error checking region: {e}")
            except ValueError:
                logger.error(f"[SOLVEY_DOCTORS] Invalid region_id format: {region_id}")
                return Response({'success': False, 'error': 'Invalid region_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        # City filter (opsional)
        city_id = request.GET.get('city_id')
        if city_id:
            try:
                city_id = int(city_id)
                doctors = doctors.filter(city_id=city_id)
                logger.info(f"[SOLVEY_DOCTORS] Filtered by city_id={city_id}, count: {doctors.count()}")
            except ValueError:
                return Response({'success': False, 'error': 'Invalid city_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Hospital filter (opsional)
        hospital_id = request.GET.get('hospital_id')
        if hospital_id:
            try:
                hospital_id = int(hospital_id)
                doctors = doctors.filter(klinika_id=hospital_id)
                logger.info(f"[SOLVEY_DOCTORS] Filtered by hospital_id={hospital_id}, count: {doctors.count()}")
            except ValueError:
                return Response({'success': False, 'error': 'Invalid hospital_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        doctors = doctors.order_by('ad')
        logger.info(f"[SOLVEY_DOCTORS] Final doctors count before processing: {doctors.count()}")
        data = []
        for d in doctors:
            # Hospital name-i tap
            hospital_name = ''
            if d.klinika_id:
                try:
                    hospital = SolveyHospital.objects.using('external').filter(id=d.klinika_id).first()
                    if hospital:
                        hospital_name = hospital.hospital_name or ''
                except Exception as e:
                    logger.error(f"[SOLVEY_DOCTORS] Error fetching hospital for doctor {d.id}: {e}")
                    pass
            
            # Dərəcə field-indən VIP və dərəcəni ayır
            # derece field-ində: VIP, I, II, III ola bilər
            derece_value = d.derece or ''
            vip_value = ''
            degree_value = ''
            
            try:
                if derece_value:
                    derece_str = str(derece_value).strip().upper()
                    # Əgər tam olaraq "VIP" və ya "VIP I", "VIP II", "VIP III" varsa
                    if derece_str == 'VIP':
                        # Yalnız VIP var, dərəcə yoxdur
                        vip_value = 'VIP'
                        degree_value = ''
                    elif derece_str.startswith('VIP'):
                        # VIP I, VIP II, VIP III formatı
                        vip_value = 'VIP'
                        # VIP-dən sonra qalan hissə dərəcədir
                        degree_value = derece_str.replace('VIP', '').strip()
                    else:
                        # Yalnız dərəcə var (I, II, III)
                        degree_value = derece_str
                        vip_value = ''
            except Exception as e:
                # Parsing xətası olsa, dərəcəni olduğu kimi saxla
                degree_value = str(derece_value).strip() if derece_value else ''
                vip_value = ''
            
            # Əvvəlki borc məlumatını al
            previous_debt_value = None
            try:
                if hasattr(d, 'previous_debt') and d.previous_debt is not None:
                    previous_debt_value = float(d.previous_debt)
            except (AttributeError, ValueError, TypeError):
                previous_debt_value = None
            
            data.append({
                'id': d.id,
                'name': d.ad or '',
                'specialty': d.ixtisas or '',
                'category': d.kategoriya or '',
                'degree': degree_value,  # Yalnız dərəcə (I, II, III)
                'vip': vip_value,  # VIP dərəcəsi (I, II, III)
                'gender': d.cinsiyyet or '',
                'region_id': d.bolge_id,
                'city_id': d.city_id,
                'hospital_id': d.klinika_id,
                'hospital': hospital_name,
                'phone': (d.number or '').strip(),
                'previous_debt': previous_debt_value  # Əvvəlki borc
            })
        logger.info(f"[SOLVEY_DOCTORS] Returning {len(data)} doctors")
        return Response({'success': True, 'data': data})
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[SOLVEY_DOCTORS] Error in get_solvey_doctors: {e}")
        logger.error(f"[SOLVEY_DOCTORS] Traceback: {error_trace}")
        return Response({'success': False, 'error': str(e), 'traceback': error_trace}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_location_permission_report(request):
    """
    Konum icazəsi rədd edildikdə istifadəçinin səbəb bildirməsi
    POST /api/location-permission-reports/
    Body: {
        "reason": "privacy|battery|not_needed|security|other",
        "reason_text": "string (optional, required if reason='other')"
    }
    """
    try:
        user = request.user
        data = request.data
        
        reason = data.get('reason')
        reason_text = data.get('reason_text', '')
        
        # Validation
        valid_reasons = ['stopped_tracking', 'location_disabled', 'privacy', 'battery', 'not_needed', 'security', 'other']
        if not reason or reason not in valid_reasons:
            return Response(
                {'success': False, 'error': f'Invalid reason. Must be one of: {valid_reasons}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if reason == 'other' and not reason_text:
            return Response(
                {'success': False, 'error': 'reason_text is required when reason is "other"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create report
        from .models import LocationPermissionReport
        report = LocationPermissionReport.objects.create(
            user=user,
            reason=reason,
            reason_text=reason_text if reason == 'other' else None
        )
        
        logger.info(f"[LOCATION_REPORT] Created report for user {user.username}: {reason}")
        
        return Response({
            'success': True,
            'message': 'Rapor uğurla göndərildi',
            'report_id': report.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"[LOCATION_REPORT] Error creating report: {e}")
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_visited_doctor(request):
    """
    Görülən həkim əlavə et
    POST /api/visited-doctors/
    Body: {
        "doctor_id": 123,
        "doctor_name": "Dr. Əli Məmmədov",
        "doctor_specialty": "Kardiologiya",
        "doctor_hospital": "Xəstəxana adı"
    }
    """
    try:
        user = request.user
        data = request.data
        
        doctor_id = data.get('doctor_id')
        doctor_name = data.get('doctor_name', '')
        doctor_specialty = data.get('doctor_specialty', '')
        doctor_hospital = data.get('doctor_hospital', '')
        
        if not doctor_id:
            return Response(
                {'success': False, 'error': 'doctor_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create visited doctor record
        from .models import VisitedDoctor
        visited_doctor = VisitedDoctor.objects.create(
            user=user,
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            doctor_specialty=doctor_specialty,
            doctor_hospital=doctor_hospital
        )
        
        logger.info(f"[VISITED_DOCTOR] Added visited doctor for user {user.username}: {doctor_name} (ID: {doctor_id})")
        
        return Response({
            'success': True,
            'message': 'Həkim görülən həkimlərə əlavə edildi',
            'visited_doctor_id': visited_doctor.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"[VISITED_DOCTOR] Error adding visited doctor: {e}")
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_visited_doctors(request):
    """
    İstifadəçinin görülən həkimlərini gətir
    GET /api/visited-doctors/
    """
    try:
        user = request.user
        from .models import VisitedDoctor
        
        visited_doctors = VisitedDoctor.objects.filter(user=user).order_by('-visit_date')
        
        data = [{
            'id': vd.id,
            'doctor_id': vd.doctor_id,
            'doctor_name': vd.doctor_name,
            'doctor_specialty': vd.doctor_specialty,
            'doctor_hospital': vd.doctor_hospital,
            'visit_date': vd.visit_date.isoformat(),
        } for vd in visited_doctors]
        
        logger.info(f"[VISITED_DOCTOR] Returning {len(data)} visited doctors for user {user.username}")
        
        return Response({
            'success': True,
            'data': data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"[VISITED_DOCTOR] Error fetching visited doctors: {e}")
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    """
    İstifadəçinin bütün aktivliklərini real-time formada qaytarır
    GET /api/dashboard/
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count, Q, Max, Min
        from django.contrib.auth.models import User
        
        user = request.user
        
        # 1. Aktiv route (konum izləmə)
        active_route = Route.objects.filter(
            user=user,
            end_time__isnull=True
        ).order_by('-start_time').first()
        
        active_route_data = None
        if active_route:
            # Son konum
            last_location = LocationPoint.objects.filter(
                route=active_route
            ).order_by('-timestamp').first()
            
            # Konum nöqtələrinin sayı
            location_count = LocationPoint.objects.filter(route=active_route).count()
            
            # Başlama zamanından indiyə qədər keçən vaxt
            duration_seconds = (timezone.now() - active_route.start_time).total_seconds()
            duration_minutes = int(duration_seconds / 60)
            duration_hours = int(duration_minutes / 60)
            
            active_route_data = {
                'id': active_route.id,
                'start_time': active_route.start_time.isoformat(),
                'start_time_formatted': active_route.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'is_online': active_route.is_online,
                'last_ping': active_route.last_ping.isoformat() if active_route.last_ping else None,
                'last_ping_formatted': active_route.last_ping.strftime('%Y-%m-%d %H:%M:%S') if active_route.last_ping else None,
                'last_location_time': active_route.last_location_time.isoformat() if active_route.last_location_time else None,
                'last_location_time_formatted': active_route.last_location_time.strftime('%Y-%m-%d %H:%M:%S') if active_route.last_location_time else None,
                'location_count': location_count,
                'duration_seconds': int(duration_seconds),
                'duration_minutes': duration_minutes,
                'duration_hours': duration_hours,
                'duration_formatted': f"{duration_hours}s {duration_minutes % 60}d",
                'last_location': {
                    'latitude': float(last_location.latitude) if last_location else None,
                    'longitude': float(last_location.longitude) if last_location else None,
                    'timestamp': last_location.timestamp.isoformat() if last_location else None,
                    'timestamp_formatted': last_location.timestamp.strftime('%Y-%m-%d %H:%M:%S') if last_location else None,
                } if last_location else None,
            }
        
        # 2. Son 30 günün route-ları (konum başlatma/bağlama)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_routes = Route.objects.filter(
            user=user,
            start_time__gte=thirty_days_ago
        ).order_by('-start_time')[:50]
        
        routes_data = []
        for route in recent_routes:
            duration_seconds = None
            if route.end_time:
                duration_seconds = (route.end_time - route.start_time).total_seconds()
            elif active_route and route.id == active_route.id:
                duration_seconds = (timezone.now() - route.start_time).total_seconds()
            
            routes_data.append({
                'id': route.id,
                'start_time': route.start_time.isoformat(),
                'start_time_formatted': route.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': route.end_time.isoformat() if route.end_time else None,
                'end_time_formatted': route.end_time.strftime('%Y-%m-%d %H:%M:%S') if route.end_time else 'Aktiv',
                'is_active': route.is_active,
                'duration_seconds': int(duration_seconds) if duration_seconds else None,
                'duration_minutes': int(duration_seconds / 60) if duration_seconds else None,
                'duration_hours': int(duration_seconds / 3600) if duration_seconds else None,
                'location_count': LocationPoint.objects.filter(route=route).count(),
            })
        
        # 3. Görülən həkimlər (son 30 gün)
        visited_doctors = VisitedDoctor.objects.filter(
            user=user,
            visit_date__gte=thirty_days_ago
        ).order_by('-visit_date', '-created_at')[:50]
        
        visited_doctors_data = []
        for doctor in visited_doctors:
            visited_doctors_data.append({
                'id': doctor.id,
                'doctor_id': doctor.doctor_id,
                'doctor_name': doctor.doctor_name,
                'doctor_specialty': doctor.doctor_specialty,
                'doctor_hospital': doctor.doctor_hospital,
                'visit_date': doctor.visit_date.isoformat(),
                'visit_date_formatted': doctor.visit_date.strftime('%Y-%m-%d %H:%M:%S'),
                'created_at': doctor.created_at.isoformat(),
                'created_at_formatted': doctor.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        # 4. Planlamalar (visit schedules)
        schedules = VisitSchedule.objects.filter(
            user=user,
            is_active=True
        ).order_by('day_of_week', 'start_time')
        
        schedules_data = []
        for schedule in schedules:
            day_names = {
                1: 'Bazar ertəsi',
                2: 'Çərşənbə axşamı',
                3: 'Çərşənbə',
                4: 'Cümə axşamı',
                5: 'Cümə',
                6: 'Şənbə',
                7: 'Bazar',
            }
            schedules_data.append({
                'id': schedule.id,
                'hospital_name': schedule.hospital_name,
                'doctor_name': schedule.doctor_name,
                'day_of_week': schedule.day_of_week,
                'day_name': day_names.get(schedule.day_of_week, ''),
                'start_time': schedule.start_time.strftime('%H:%M') if schedule.start_time else None,
                'end_time': schedule.end_time.strftime('%H:%M') if schedule.end_time else None,
                'notes': schedule.notes,
                'created_at': schedule.created_at.isoformat(),
                'created_at_formatted': schedule.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        # 5. Konum icazəsi rədd etmələri (location permission reports)
        location_reports = LocationPermissionReport.objects.filter(
            user=user
        ).order_by('-timestamp')[:20]
        
        location_reports_data = []
        for report in location_reports:
            location_reports_data.append({
                'id': report.id,
                'reason': report.reason,
                'reason_display': report.get_reason_display(),
                'reason_text': report.reason_text,
                'timestamp': report.timestamp.isoformat(),
                'timestamp_formatted': report.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        # 6. Statistika
        total_routes = Route.objects.filter(user=user).count()
        total_locations = LocationPoint.objects.filter(route__user=user).count()
        total_visited_doctors = VisitedDoctor.objects.filter(user=user).count()
        total_schedules = VisitSchedule.objects.filter(user=user, is_active=True).count()
        
        # Son login zamanı (User model-dən)
        # Qeyd: Django User model-də last_login var, amma bizim sistemdə JWT istifadə edirik
        # Ona görə də bu məlumatı JWT token-dan və ya ayrıca model-dən götürmək lazımdır
        # İndi sadəcə user.date_joined istifadə edək
        
        stats = {
            'total_routes': total_routes,
            'total_locations': total_locations,
            'total_visited_doctors': total_visited_doctors,
            'total_schedules': total_schedules,
            'user_joined': user.date_joined.isoformat(),
            'user_joined_formatted': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # 7. Real-time status
        current_time = timezone.now()
        realtime_status = {
            'current_time': current_time.isoformat(),
            'current_time_formatted': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'has_active_route': active_route is not None,
            'is_online': active_route.is_online if active_route else False,
        }
        
        return Response({
            'success': True,
            'data': {
                'active_route': active_route_data,
                'recent_routes': routes_data,
                'visited_doctors': visited_doctors_data,
                'schedules': schedules_data,
                'location_reports': location_reports_data,
                'stats': stats,
                'realtime_status': realtime_status,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[DASHBOARD] Error in user_dashboard: {e}\nTraceback: {error_trace}")
        return Response(
            {'success': False, 'error': str(e), 'traceback': error_trace},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_medicines(request):
    """
    Solvey database-dən aktiv dərmanların siyahısını qaytarır
    GET /api/medicines/
    """
    try:
        logger.info("[SOLVEY_MEDICINES] Starting get_medicines")
        
        # Cədvəl adını environment variable-dan al
        import os
        medicines_table = os.getenv('SOLVEY_MEDICINES_TABLE', 'tracking_medical')
        
        # Raw SQL query ilə dərmanları çək
        from django.db import connections
        with connections['external'].cursor() as cursor:
            # Əvvəlcə cədvəlin mövcud olub-olmadığını yoxla
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND (table_name = %s OR table_name = %s OR table_name = %s OR table_name = %s)
                LIMIT 1
            """, ['medical', 'tracking_medical', 'medicines', 'tracking_medicines'])
            
            table_row = cursor.fetchone()
            if table_row:
                actual_table_name = table_row[0]
                logger.info(f"[SOLVEY_MEDICINES] Found table: {actual_table_name}")
            else:
                # Cədvəl tapılmadı, boş siyahı qaytar
                logger.warning(f"[SOLVEY_MEDICINES] Medicine table not found. Tried: medical, tracking_medical, medicines, tracking_medicines")
                return Response({
                    'success': True,
                    'count': 0,
                    'data': [],
                    'message': 'Dərmanlar cədvəli tapılmadı'
                })
            
            # Dərmanları çək
            cursor.execute(f"""
                SELECT id, med_name, med_full_name, med_price, komissiya, status
                FROM "{actual_table_name}"
                WHERE status = true
                ORDER BY med_name
            """)
            
            columns = [col[0] for col in cursor.description]
            medicines_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        logger.info(f"[SOLVEY_MEDICINES] Found {len(medicines_data)} medicines")
        
        data = []
        for med in medicines_data:
            med_id = med['id']
            # Local Medicine modelindən annotasiya məlumatını çək
            annotation_data = {}
            try:
                local_medicine = Medicine.objects.filter(solvey_id=med_id).first()
                if local_medicine:
                    annotation_data = {
                        'annotation': local_medicine.annotation or '',
                        'active_ingredient': local_medicine.active_ingredient or '',
                        'dosage': local_medicine.dosage or '',
                        'indications': local_medicine.indications or '',
                        'contraindications': local_medicine.contraindications or '',
                        'side_effects': local_medicine.side_effects or '',
                        'storage_conditions': local_medicine.storage_conditions or '',
                        'manufacturer': local_medicine.manufacturer or '',
                        'barcode': local_medicine.barcode or '',
                        'image': local_medicine.image.url if local_medicine.image else None,
                    }
            except Exception as e:
                logger.warning(f"[SOLVEY_MEDICINES] Could not fetch local annotation for medicine {med_id}: {e}")
            
            data.append({
                'id': med_id,
                'name': med.get('med_name') or '',
                'name_az': med.get('med_full_name') or med.get('med_name') or '',
                'price': float(med['med_price']) if med.get('med_price') else None,
                'komissiya': float(med['komissiya']) if med.get('komissiya') else None,
                'description': med.get('med_full_name') or med.get('med_name') or '',
                'annotation': annotation_data.get('annotation', ''),
                'active_ingredient': annotation_data.get('active_ingredient', ''),
                'dosage': annotation_data.get('dosage', ''),
                'indications': annotation_data.get('indications', ''),
                'contraindications': annotation_data.get('contraindications', ''),
                'side_effects': annotation_data.get('side_effects', ''),
                'storage_conditions': annotation_data.get('storage_conditions', ''),
                'manufacturer': annotation_data.get('manufacturer', ''),
                'barcode': annotation_data.get('barcode', ''),
                'image': annotation_data.get('image'),
                'is_active': med.get('status', True),
            })
        
        logger.info(f"[SOLVEY_MEDICINES] Returning {len(data)} medicines")
        return Response({
            'success': True,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[SOLVEY_MEDICINES] Error fetching medicines: {e}")
        logger.error(f"[SOLVEY_MEDICINES] Traceback: {error_trace}")
        return Response({
            'success': False,
            'error': str(e),
            'traceback': error_trace
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_medicine_detail(request, medicine_id):
    """
    Solvey database-dən dərmanın detallı məlumatını qaytarır
    GET /api/medicines/{id}/
    """
    try:
        logger.info(f"[SOLVEY_MEDICINES] Fetching medicine detail for ID: {medicine_id}")
        
        # Cədvəl adını tap
        import os
        from django.db import connections
        with connections['external'].cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND (table_name = %s OR table_name = %s OR table_name = %s OR table_name = %s)
                LIMIT 1
            """, ['medical', 'tracking_medical', 'medicines', 'tracking_medicines'])
            
            table_row = cursor.fetchone()
            if not table_row:
                return Response({
                    'success': False,
                    'error': 'Dərmanlar cədvəli tapılmadı'
                }, status=status.HTTP_404_NOT_FOUND)
            
            actual_table_name = table_row[0]
            
            # Dərmanı çək
            cursor.execute(f"""
                SELECT id, med_name, med_full_name, med_price, komissiya, status
                FROM "{actual_table_name}"
                WHERE id = %s AND status = true
            """, [medicine_id])
            
            med_row = cursor.fetchone()
            if not med_row:
                return Response({
                    'success': False,
                    'error': 'Dərman tapılmadı'
                }, status=status.HTTP_404_NOT_FOUND)
            
            columns = [col[0] for col in cursor.description]
            med = dict(zip(columns, med_row))
        
        # Əgər annotasiya bizim Medicine modelində varsa, onu da çək
        annotation_data = ''
        try:
            local_medicine = Medicine.objects.filter(solvey_id=medicine_id).first()
            if local_medicine:
                annotation_data = local_medicine.annotation or ''
        except Exception as e:
            logger.warning(f"[SOLVEY_MEDICINES] Could not fetch local annotation: {e}")
        
        data = {
            'id': med['id'],
            'name': med.get('med_name') or '',
            'name_az': med.get('med_full_name') or med.get('med_name') or '',
            'price': float(med['med_price']) if med.get('med_price') else None,
            'komissiya': float(med['komissiya']) if med.get('komissiya') else None,
            'description': med.get('med_full_name') or med.get('med_name') or '',
            'annotation': annotation_data,  # Annotasiya bizim Medicine modelindən gəlir
            'active_ingredient': '',
            'dosage': '',
            'indications': '',
            'contraindications': '',
            'side_effects': '',
            'storage_conditions': '',
            'manufacturer': '',
            'barcode': '',
            'image': None,
            'is_active': med.get('status', True),
        }
        
        # Əgər local Medicine modelində məlumat varsa, onu da əlavə et
        try:
            local_medicine = Medicine.objects.filter(solvey_id=medicine_id).first()
            if local_medicine:
                data.update({
                    'annotation': local_medicine.annotation or '',
                    'active_ingredient': local_medicine.active_ingredient or '',
                    'dosage': local_medicine.dosage or '',
                    'indications': local_medicine.indications or '',
                    'contraindications': local_medicine.contraindications or '',
                    'side_effects': local_medicine.side_effects or '',
                    'storage_conditions': local_medicine.storage_conditions or '',
                    'manufacturer': local_medicine.manufacturer or '',
                    'barcode': local_medicine.barcode or '',
                    'image': local_medicine.image.url if local_medicine.image else None,
                })
        except Exception as e:
            logger.warning(f"[SOLVEY_MEDICINES] Could not fetch local medicine data: {e}")
        
        logger.info(f"[SOLVEY_MEDICINES] Returning medicine detail for ID: {medicine_id}")
        return Response({
            'success': True,
            'data': data
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[SOLVEY_MEDICINES] Error fetching medicine {medicine_id}: {e}")
        logger.error(f"[SOLVEY_MEDICINES] Traceback: {error_trace}")
        return Response({
            'success': False,
            'error': str(e),
            'traceback': error_trace
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)