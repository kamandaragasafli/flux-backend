from django.contrib import admin

from .models import FitlogProfile


@admin.register(FitlogProfile)
class FitlogProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "updated_at")
    search_fields = ("user__email", "user__username")
    readonly_fields = ("updated_at",)
