from django.conf import settings
from django.db import models


class FitlogProfile(models.Model):
    """
    Mobil tətbiqdəki AppSettings (onboarding, dietPlan və s.) — JSON kimi saxlanılır.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fitlog_profile",
        primary_key=True,
    )
    app_settings = models.JSONField(default=dict, blank=True)
    diary_entries = models.JSONField(default=list, blank=True)
    custom_foods = models.JSONField(default=list, blank=True)
    water_entries = models.JSONField(default=list, blank=True)
    recipes = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fitlog profili"
        verbose_name_plural = "Fitlog profilləri"

    def __str__(self) -> str:
        return f"FitlogProfile(user_id={self.user_id})"
