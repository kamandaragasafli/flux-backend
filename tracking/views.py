from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db.models import Max, Count, Q
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from datetime import timedelta
import requests
import os

from .models import Route, LocationPoint
from .serializers import (
    LoginSerializer,
    RouteSerializer,
    StartRouteSerializer,
    StopRouteSerializer,
    CreateLocationSerializer,
)

# SSL uyarılarını bastır (development için)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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


class CreateLocationView(generics.CreateAPIView):
    serializer_class = CreateLocationSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class RouteDetailView(generics.RetrieveAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer


class CurrentUserView(APIView):
    """Mevcut kullanıcının bilgilerini döndürür ve günceller"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })

    def patch(self, request):
        """Kullanıcı bilgilerini günceller"""
        user = request.user
        data = request.data

        # Güncellenebilir alanlar
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']

        try:
            user.save()
            return Response({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class LastLocationsView(APIView):
    """Tüm kullanıcıların son konumlarını döndürür (harita için)"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Her kullanıcının son konumunu al
        users = User.objects.all()
        features = []
        
        for user in users:
            # Kullanıcının en son location point'ini al
            last_location = LocationPoint.objects.filter(
                route__user=user
            ).order_by('-timestamp').first()
            
            if last_location:
                features.append({
                    "id": user.id,
                    "ad": user.username,
                    "lat": float(last_location.latitude),
                    "lng": float(last_location.longitude),
                })
        
        return Response({
            "features": features
        })


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
        last_activity=Max('routes__start_time')
    ).order_by('-date_joined')[:50]
    
    # Aktif route'lar
    active_routes_list = Route.objects.filter(
        end_time__isnull=True
    ).select_related('user').prefetch_related('points').order_by('-start_time')[:20]
    
    # Son location point'ler
    recent_locations = LocationPoint.objects.select_related(
        'route__user'
    ).order_by('-timestamp')[:50]
    
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
        'recent_locations': recent_locations,
    }
    
    return render(request, 'dashboard.html', context)
