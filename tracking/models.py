from django.conf import settings
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Kullanıcı profil bilgileri - bölge ve şehir seçimleri"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    regions = models.JSONField(default=list, blank=True)  # Maksimum 3 bölge
    cities = models.JSONField(default=list, blank=True)   # Maksimum 3 şehir
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self) -> str:
        return f"{self.user.username} - Profile"


class Route(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="routes"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    is_paused = models.BooleanField(default=False)  # Duraklatma durumu
    paused_at = models.DateTimeField(null=True, blank=True)  # En son ne zaman duraklatıldı
    total_paused_duration = models.IntegerField(default=0)  # Toplam duraklatma süresi (saniye)
    last_location_time = models.DateTimeField(null=True, blank=True)  # Son konum zamanı
    
    # Bağlantı durumu
    is_online = models.BooleanField(default=True)
    last_ping = models.DateTimeField(null=True, blank=True)  # Son sinyal zamanı

    def __str__(self) -> str:
        return f"Route {self.id} for {self.user} ({self.start_time} - {self.end_time})"
    
    @property
    def is_active(self):
        """Route aktif mi?"""
        return self.end_time is None
    
    @property
    def connection_status(self):
        """Bağlantı durumu - son 30 saniyede sinyal var mı?"""
        if not self.last_ping:
            return 'unknown'
        from django.utils import timezone
        from datetime import timedelta
        if timezone.now() - self.last_ping > timedelta(seconds=30):
            return 'offline'
        return 'online'


class LocationPoint(models.Model):
    route = models.ForeignKey(
        Route, on_delete=models.CASCADE, related_name="points"
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField()
    accuracy = models.FloatField(null=True, blank=True)  # GPS hassasiyeti (metre)
    speed = models.FloatField(null=True, blank=True)  # Hız (m/s)
    battery_level = models.IntegerField(null=True, blank=True)  # Batarya seviyesi (%)
    is_online = models.BooleanField(default=True)  # İnternet bağlantısı var mı?

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=['route', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self) -> str:
        return f"{self.latitude},{self.longitude} @ {self.timestamp}"


class VisitSchedule(models.Model):
    """Haftalık hastane ziyaret planlaması"""
    
    DAY_CHOICES = [
        (1, 'Bazar ertəsi'),
        (2, 'Çərşənbə axşamı'),
        (3, 'Çərşənbə'),
        (4, 'Cümə axşamı'),
        (5, 'Cümə'),
        (6, 'Şənbə'),
        (7, 'Bazar'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="visit_schedules"
    )
    hospital_name = models.CharField(max_length=255)
    hospital_latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    hospital_longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    doctor_name = models.CharField(max_length=255, blank=True)
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self) -> str:
        day_name = dict(self.DAY_CHOICES).get(self.day_of_week, '')
        return f"{self.hospital_name} - {day_name} ({self.doctor_name})"


class HospitalVisit(models.Model):
    """Gerçekleşen hastane ziyaretleri"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hospital_visits"
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="visits",
        null=True,
        blank=True
    )
    hospital_name = models.CharField(max_length=255)
    hospital_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    hospital_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    doctor_name = models.CharField(max_length=255, blank=True)
    visit_date = models.DateField()
    check_in_time = models.TimeField()
    check_out_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)  # Dakika cinsinden
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-visit_date', '-check_in_time']

    def __str__(self) -> str:
        return f"{self.hospital_name} - {self.visit_date} ({self.doctor_name})"
    
    def calculate_duration(self):
        """Ziyaret süresini hesapla"""
        if self.check_in_time and self.check_out_time:
            from datetime import datetime, timedelta
            check_in = datetime.combine(datetime.today(), self.check_in_time)
            check_out = datetime.combine(datetime.today(), self.check_out_time)
            delta = check_out - check_in
            self.duration_minutes = int(delta.total_seconds() / 60)
            return self.duration_minutes
        return None


class Notification(models.Model):
    """Kullanıcı bildirimleri - dashboard'dan veya sistem tarafından"""
    
    TYPE_CHOICES = [
        ('info', 'Bilgi'),
        ('warning', 'Uyarı'),
        ('error', 'Hata'),
        ('message', 'Mesaj'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Bildirim ile ilişkili konum/route (opsiyonel)
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return f"{self.notification_type.upper()} - {self.user.username}: {self.title}"


class LocationPermissionReport(models.Model):
    """Konum icazəsi rədd edildikdə istifadəçinin səbəb bildirməsi"""
    
    REASON_CHOICES = [
        ('stopped_tracking', 'İzləməni dayandırdım'),
        ('location_disabled', 'Telefonun konumunu bağladım'),
        ('privacy', 'Məxfilik narahatlığı'),
        ('battery', 'Batareya istehlakı'),
        ('not_needed', 'İstifadə etmirəm'),
        ('security', 'Təhlükəsizlik narahatlığı'),
        ('other', 'Digər'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="location_permission_reports"
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    reason_text = models.TextField(blank=True, null=True)  # Digər səbəb üçün
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Location Permission Report"
        verbose_name_plural = "Location Permission Reports"
    
    def __str__(self) -> str:
        return f"{self.user.username} - {self.get_reason_display()} ({self.timestamp})"