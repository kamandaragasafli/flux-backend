"""
Fitlog mobil API (JWT):
GET/PUT  /api/me/settings/
GET/PUT  /api/me/diary/
GET/PUT  /api/me/custom-foods/
GET/PUT  /api/me/water/
GET/PUT  /api/me/recipes/
"""

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import FitlogProfile
from .serializers import parse_app_settings_dict, parse_json_array

FITLOG_PROFILE_DEFAULTS = {
    "app_settings": {},
    "diary_entries": [],
    "custom_foods": [],
    "water_entries": [],
    "recipes": [],
}


def _unwrap_settings_payload(data):
    """{ \"settings\": {...} } və ya birbaşa {...} qəbul edir."""
    if isinstance(data, dict) and "settings" in data:
        return data["settings"]
    return data


def _unwrap_entries_payload(data, key: str):
    """{ \"entries\": [...] } və ya birbaşa massiv."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and key in data:
        return data[key]
    return data


def _unwrap_foods_payload(data):
    """{ \"foods\": [...] } və ya birbaşa massiv."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "foods" in data:
        return data["foods"]
    return data


def _unwrap_recipes_payload(data):
    """{ \"recipes\": [...] } və ya birbaşa massiv."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "recipes" in data:
        return data["recipes"]
    return data


@api_view(["GET", "PUT"])
@permission_classes([permissions.IsAuthenticated])
def me_settings(request):
    profile, _ = FitlogProfile.objects.get_or_create(
        user=request.user,
        defaults={**FITLOG_PROFILE_DEFAULTS},
    )

    if request.method == "GET":
        return Response(
            {"settings": profile.app_settings if isinstance(profile.app_settings, dict) else {}},
            status=status.HTTP_200_OK,
        )

    raw = _unwrap_settings_payload(request.data)
    profile.app_settings = parse_app_settings_dict(raw)
    profile.save(update_fields=["app_settings", "updated_at"])
    return Response(
        {"settings": profile.app_settings},
        status=status.HTTP_200_OK,
    )


@api_view(["GET", "PUT"])
@permission_classes([permissions.IsAuthenticated])
def me_diary(request):
    profile, _ = FitlogProfile.objects.get_or_create(
        user=request.user,
        defaults={**FITLOG_PROFILE_DEFAULTS},
    )

    if request.method == "GET":
        rows = profile.diary_entries if isinstance(profile.diary_entries, list) else []
        return Response({"entries": rows}, status=status.HTTP_200_OK)

    raw = _unwrap_entries_payload(request.data, "entries")
    profile.diary_entries = parse_json_array(raw)
    profile.save(update_fields=["diary_entries", "updated_at"])
    return Response({"entries": profile.diary_entries}, status=status.HTTP_200_OK)


@api_view(["GET", "PUT"])
@permission_classes([permissions.IsAuthenticated])
def me_custom_foods(request):
    profile, _ = FitlogProfile.objects.get_or_create(
        user=request.user,
        defaults={**FITLOG_PROFILE_DEFAULTS},
    )

    if request.method == "GET":
        rows = profile.custom_foods if isinstance(profile.custom_foods, list) else []
        return Response({"foods": rows}, status=status.HTTP_200_OK)

    raw = _unwrap_foods_payload(request.data)
    profile.custom_foods = parse_json_array(raw)
    profile.save(update_fields=["custom_foods", "updated_at"])
    return Response({"foods": profile.custom_foods}, status=status.HTTP_200_OK)


@api_view(["GET", "PUT"])
@permission_classes([permissions.IsAuthenticated])
def me_water(request):
    profile, _ = FitlogProfile.objects.get_or_create(
        user=request.user,
        defaults={**FITLOG_PROFILE_DEFAULTS},
    )

    if request.method == "GET":
        rows = profile.water_entries if isinstance(profile.water_entries, list) else []
        return Response({"entries": rows}, status=status.HTTP_200_OK)

    raw = _unwrap_entries_payload(request.data, "entries")
    profile.water_entries = parse_json_array(raw)
    profile.save(update_fields=["water_entries", "updated_at"])
    return Response({"entries": profile.water_entries}, status=status.HTTP_200_OK)


@api_view(["GET", "PUT"])
@permission_classes([permissions.IsAuthenticated])
def me_recipes(request):
    profile, _ = FitlogProfile.objects.get_or_create(
        user=request.user,
        defaults={**FITLOG_PROFILE_DEFAULTS},
    )

    if request.method == "GET":
        rows = profile.recipes if isinstance(profile.recipes, list) else []
        return Response({"recipes": rows}, status=status.HTTP_200_OK)

    raw = _unwrap_recipes_payload(request.data)
    profile.recipes = parse_json_array(raw)
    profile.save(update_fields=["recipes", "updated_at"])
    return Response({"recipes": profile.recipes}, status=status.HTTP_200_OK)
