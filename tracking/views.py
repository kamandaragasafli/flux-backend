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

from .models import Route, LocationPoint, VisitSchedule, HospitalVisit, UserProfile, Notification
from .models_solvey import SolveyRegion, SolveyCity, SolveyHospital, SolveyDoctor
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
)

# SSL uyarılarını bastır (development için)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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


# Admin Dashboard View
def is_staff_user(user):
    return user.is_staff or user.is_superuser


@user_passes_test(is_staff_user)
def admin_dashboard(request):
    """Özelleştirilmiş admin dashboard"""
    
    # İstatistikler
    total_users = User.objects.count()
    active_users = User.objects.filter(routes__end_time__isnull=True).distinct().count()
    total_routes = Route.objects.count()
    active_routes = Route.objects.filter(end_time__isnull=True).count()
    total_locations = LocationPoint.objects.count()
    
    # Son 24 saat
    last_24h = timezone.now() - timedelta(hours=24)
    routes_last_24h = Route.objects.filter(start_time__gte=last_24h).count()
    locations_last_24h = LocationPoint.objects.filter(timestamp__gte=last_24h).count()
    
    # Kullanıcılar listesi
    users = User.objects.annotate(
        route_count=Count('routes'),
        location_count=Count('routes__points'),
        last_activity=Max('routes__start_time'),
        has_active_route=Count('routes', filter=Q(routes__end_time__isnull=True))
    ).order_by('-date_joined')[:50]
    
    # Aktif route'lar - bağlantı durumları ile
    active_routes_list = Route.objects.filter(
        end_time__isnull=True
    ).select_related('user').prefetch_related('points').order_by('-start_time')[:20]
    
    # Her route için ek bilgiler
    routes_data = []
    for route in active_routes_list:
        last_point = route.points.last()
        routes_data.append({
            'route': route,
            'last_point': last_point,
            'connection_status': route.connection_status,
            'is_paused': route.is_paused,
            'point_count': route.points.count(),
        })
    
    # Son location point'ler
    recent_locations = LocationPoint.objects.select_related(
        'route__user'
    ).order_by('-timestamp')[:50]
    
    # Son bildirimler (tüm kullanıcılar için - admin görüntülemesi)
    recent_notifications = Notification.objects.select_related(
        'user'
    ).order_by('-created_at')[:50]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'total_routes': total_routes,
        'active_routes': active_routes,
        'total_locations': total_locations,
        'routes_last_24h': routes_last_24h,
        'locations_last_24h': locations_last_24h,
        'users': users,
        'active_routes_list': active_routes_list,
        'routes_data': routes_data,
        'recent_locations': recent_locations,
        'recent_notifications': recent_notifications,
    }
    
    return render(request, 'dashboard.html', context)


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
        regions = SolveyRegion.objects.all().order_by('region_name')
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
        cities = SolveyCity.objects.all()
        
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
        hospitals = SolveyHospital.objects.all()
        
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
        doctors = SolveyDoctor.objects.all()
        
        # Region filter (opsional)
        region_id = request.GET.get('region_id')
        if region_id:
            try:
                region_id = int(region_id)
                doctors = doctors.filter(bolge_id=region_id)
            except ValueError:
                return Response({'success': False, 'error': 'Invalid region_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        # City filter (opsional)
        city_id = request.GET.get('city_id')
        if city_id:
            try:
                city_id = int(city_id)
                doctors = doctors.filter(city_id=city_id)
            except ValueError:
                return Response({'success': False, 'error': 'Invalid city_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Hospital filter (opsional)
        hospital_id = request.GET.get('hospital_id')
        if hospital_id:
            try:
                hospital_id = int(hospital_id)
                doctors = doctors.filter(klinika_id=hospital_id)
            except ValueError:
                return Response({'success': False, 'error': 'Invalid hospital_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        doctors = doctors.order_by('ad')
        data = []
        for d in doctors:
            # Hospital name-i tap
            hospital_name = ''
            if d.klinika_id:
                try:
                    hospital = SolveyHospital.objects.filter(id=d.klinika_id).first()
                    if hospital:
                        hospital_name = hospital.hospital_name or ''
                except Exception:
                    pass
            
            data.append({
                'id': d.id,
                'name': d.ad or '',
                'specialty': d.ixtisas or '',
                'category': d.kategoriya or '',
                'degree': d.derece or '',
                'vip': (d.vip or '').strip() if hasattr(d, 'vip') else '',  # VIP field-i
                'gender': d.cinsiyyet or '',
                'region_id': d.bolge_id,
                'city_id': d.city_id,
                'hospital_id': d.klinika_id,
                'hospital': hospital_name,
                'phone': (d.number or '').strip()
            })
        return Response({'success': True, 'data': data})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
