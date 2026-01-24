from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import Route, LocationPoint, VisitSchedule, HospitalVisit, UserProfile, Notification


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'regions', 'cities', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_regions(self, value):
        if len(value) > 3:
            raise serializers.ValidationError("Maksimum 3 bölge seçebilirsiniz.")
        return value
    
    def validate_cities(self, value):
        if len(value) > 3:
            raise serializers.ValidationError("Maksimum 3 şehir seçebilirsiniz.")
        return value


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        username = attrs.get("username")
        email = attrs.get("email", "")
        password = attrs.get("password")
        password2 = attrs.get("password2")

        # Username tələb olunur
        if not username or not username.strip():
            raise serializers.ValidationError("İstifadəçi adı tələb olunur.")
        
        # Şifrələr eyni olmalıdır
        if password != password2:
            raise serializers.ValidationError("Şifrələr eyni olmalıdır.")
        
        # Username artıq mövcuddursa
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("Bu istifadəçi adı artıq mövcuddur.")
        
        # Email varsa və artıq mövcuddursa
        if email and email.strip() and User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Bu email artıq mövcuddur.")
        
        attrs["username"] = username.strip()
        attrs["password"] = password
        return attrs

    def create(self, validated_data):
        username = validated_data["username"]
        email = validated_data.get("email", "")
        password = validated_data["password"]
        
        # Email yoxdursa, default email yarat
        if not email or not email.strip():
            email = f"{username}@flux.local"
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # UserProfile yarat
        UserProfile.objects.get_or_create(user=user)
        
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username", "").strip()  # Boşluqları təmizlə
        password = attrs.get("password", "").strip()  # Boşluqları təmizlə
        
        if not username or not password:
            raise serializers.ValidationError("Username və şifrə tələb olunur.")
        
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
    accuracy = serializers.FloatField(required=False)
    speed = serializers.FloatField(required=False)
    battery_level = serializers.IntegerField(required=False)
    is_online = serializers.BooleanField(required=False, default=True)

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
        from django.utils import timezone
        route = validated_data["route"]
        latitude = validated_data["latitude"]
        longitude = validated_data["longitude"]
        timestamp = validated_data["timestamp"]
        accuracy = validated_data.get("accuracy")
        speed = validated_data.get("speed")
        battery_level = validated_data.get("battery_level")
        is_online = validated_data.get("is_online", True)
        
        # Route'un son konum zamanını ve ping'ini güncelle
        route.last_location_time = timestamp
        route.last_ping = timezone.now()
        route.is_online = is_online
        route.save(update_fields=['last_location_time', 'last_ping', 'is_online'])
        
        return LocationPoint.objects.create(
            route=route,
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
            accuracy=accuracy,
            speed=speed,
            battery_level=battery_level,
            is_online=is_online,
        )


class VisitScheduleSerializer(serializers.ModelSerializer):
    day_name = serializers.SerializerMethodField()
    
    class Meta:
        model = VisitSchedule
        fields = [
            'id',
            'hospital_name',
            'hospital_latitude',
            'hospital_longitude',
            'doctor_name',
            'day_of_week',
            'day_name',
            'start_time',
            'end_time',
            'notes',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_day_name(self, obj):
        return dict(VisitSchedule.DAY_CHOICES).get(obj.day_of_week, '')
    
    def create(self, validated_data):
        user = self.context['request'].user
        return VisitSchedule.objects.create(user=user, **validated_data)


class HospitalVisitSerializer(serializers.ModelSerializer):
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = HospitalVisit
        fields = [
            'id',
            'hospital_name',
            'hospital_latitude',
            'hospital_longitude',
            'doctor_name',
            'visit_date',
            'check_in_time',
            'check_out_time',
            'duration_minutes',
            'duration_display',
            'notes',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'duration_minutes']
    
    def get_duration_display(self, obj):
        if obj.duration_minutes:
            hours = obj.duration_minutes // 60
            minutes = obj.duration_minutes % 60
            if hours > 0:
                return f"{hours} saat {minutes} dəqiqə"
            return f"{minutes} dəqiqə"
        return "-"
    
    def create(self, validated_data):
        user = self.context['request'].user
        visit = HospitalVisit.objects.create(user=user, **validated_data)
        visit.calculate_duration()
        visit.save()
        return visit
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.calculate_duration()
        instance.save()
        return instance


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('user', 'created_at')
