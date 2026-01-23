from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Route, LocationPoint, VisitSchedule, HospitalVisit, UserProfile, Notification


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'start_time', 'end_time', 'duration', 'point_count']
    list_filter = ['start_time', 'end_time']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['start_time']
    date_hierarchy = 'start_time'
    
    def duration(self, obj):
        if obj.end_time and obj.start_time:
            delta = obj.end_time - obj.start_time
            hours = delta.total_seconds() / 3600
            return f"{hours:.2f} saat"
        return "Aktiv"
    duration.short_description = "Müddət"
    
    def point_count(self, obj):
        return obj.points.count()
    point_count.short_description = "Nöqtə Sayı"


@admin.register(LocationPoint)
class LocationPointAdmin(admin.ModelAdmin):
    list_display = ['id', 'route', 'latitude', 'longitude', 'timestamp']
    list_filter = ['timestamp', 'route__user']
    search_fields = ['route__user__username', 'latitude', 'longitude']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    raw_id_fields = ['route']


@admin.register(VisitSchedule)
class VisitScheduleAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'hospital_name', 'doctor_name', 'day_of_week_display', 'time_range', 'is_active']
    list_filter = ['user', 'day_of_week', 'is_active', 'created_at']
    search_fields = ['user__username', 'hospital_name', 'doctor_name']
    ordering = ['user', 'day_of_week', 'start_time']
    readonly_fields = ['created_at', 'updated_at']
    
    def day_of_week_display(self, obj):
        return dict(obj.DAY_CHOICES).get(obj.day_of_week, '')
    day_of_week_display.short_description = "Gün"
    
    def time_range(self, obj):
        if obj.start_time and obj.end_time:
            return f"{obj.start_time} - {obj.end_time}"
        elif obj.start_time:
            return str(obj.start_time)
        return "-"
    time_range.short_description = "Vaxt"


@admin.register(HospitalVisit)
class HospitalVisitAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'hospital_name', 'doctor_name', 'visit_date', 'time_range', 'duration_display']
    list_filter = ['user', 'visit_date', 'created_at']
    search_fields = ['user__username', 'hospital_name', 'doctor_name']
    ordering = ['-visit_date', '-check_in_time']
    readonly_fields = ['created_at', 'updated_at', 'duration_minutes']
    date_hierarchy = 'visit_date'
    
    def time_range(self, obj):
        if obj.check_in_time and obj.check_out_time:
            return f"{obj.check_in_time} - {obj.check_out_time}"
        elif obj.check_in_time:
            return str(obj.check_in_time)
        return "-"
    time_range.short_description = "Vaxt Aralığı"
    
    def duration_display(self, obj):
        if obj.duration_minutes:
            hours = obj.duration_minutes // 60
            minutes = obj.duration_minutes % 60
            if hours > 0:
                return f"{hours}s {minutes}d"
            return f"{minutes}d"
        return "-"
    duration_display.short_description = "Müddət"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'regions_display', 'cities_display', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def regions_display(self, obj):
        return ', '.join(obj.regions) if obj.regions else '-'
    regions_display.short_description = "Bölgələr"
    
    def cities_display(self, obj):
        return ', '.join(obj.cities) if obj.cities else '-'
    cities_display.short_description = "Şəhərlər"


# Custom User Admin
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'route_count', 'profile_completed', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    
    def route_count(self, obj):
        return obj.routes.count()
    route_count.short_description = "Marşrut Sayı"
    
    def profile_completed(self, obj):
        try:
            profile = obj.profile
            return len(profile.regions) > 0 and len(profile.cities) > 0
        except UserProfile.DoesNotExist:
            return False
    profile_completed.boolean = True
    profile_completed.short_description = "Profil Tamamlandı"


# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Customize admin site
admin.site.site_header = "Solvey Tracker Admin Panel"
admin.site.site_title = "Solvey Admin"
admin.site.index_title = "İdarəetmə Paneli"

