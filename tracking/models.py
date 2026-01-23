from django.conf import settings
from django.db import models


class Route(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="routes"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Route {self.id} for {self.user} ({self.start_time} - {self.end_time})"


class LocationPoint(models.Model):
    route = models.ForeignKey(
        Route, on_delete=models.CASCADE, related_name="points"
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField()

    class Meta:
        ordering = ["timestamp"]

    def __str__(self) -> str:
        return f"{self.latitude},{self.longitude} @ {self.timestamp}"


