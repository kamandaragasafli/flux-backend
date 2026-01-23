from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Route, LocationPoint


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


# Custom User Admin
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'route_count', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    
    def route_count(self, obj):
        return obj.routes.count()
    route_count.short_description = "Marşrut Sayı"


# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Customize admin site
admin.site.site_header = "Solvey Tracker Admin Panel"
admin.site.site_title = "Solvey Admin"
admin.site.index_title = "İdarəetmə Paneli"

