from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import Route, LocationPoint


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        attrs["user"] = user
        return attrs


class LocationPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationPoint
        fields = ["id", "latitude", "longitude", "timestamp"]


class RouteSerializer(serializers.ModelSerializer):
    points = LocationPointSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = ["id", "start_time", "end_time", "points"]


class StartRouteSerializer(serializers.Serializer):
    def create(self, validated_data):
        user = self.context["request"].user
        # Only allow one active (no end_time) route
        active = Route.objects.filter(user=user, end_time__isnull=True).first()
        if active:
            return active
        return Route.objects.create(user=user, start_time=timezone.now())


class StopRouteSerializer(serializers.Serializer):
    def save(self, **kwargs):
        user = self.context["request"].user
        route = (
            Route.objects.filter(user=user, end_time__isnull=True)
            .order_by("-start_time")
            .first()
        )
        if not route:
            raise serializers.ValidationError("No active route to stop.")
        route.end_time = timezone.now()
        route.save(update_fields=["end_time"])
        return route


class CreateLocationSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    timestamp = serializers.DateTimeField()

    def validate(self, attrs):
        user = self.context["request"].user
        route = (
            Route.objects.filter(user=user, end_time__isnull=True)
            .order_by("-start_time")
            .first()
        )
        if not route:
            raise serializers.ValidationError(
                "No active route. Call /api/routes/start/ first."
            )
        attrs["route"] = route
        return attrs

    def create(self, validated_data):
        route = validated_data["route"]
        latitude = validated_data["latitude"]
        longitude = validated_data["longitude"]
        timestamp = validated_data["timestamp"]
        return LocationPoint.objects.create(
            route=route,
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
        )


