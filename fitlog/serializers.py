from rest_framework.serializers import ValidationError


def parse_app_settings_dict(data):
    """Mobil JSON obyektini qəbul edir (None → {})."""
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    raise ValidationError("settings obyekt olmalıdır.")


def parse_json_array(data):
    """Gündəlik qeydləri / xüsusi qidalar massivi (None → [])."""
    if data is None:
        return []
    if isinstance(data, list):
        return data
    raise ValidationError("JSON massiv olmalıdır.")
