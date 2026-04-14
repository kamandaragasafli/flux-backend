"""
Fitlog mobil üçün: email/qeydiyyat, Google id_token, JWT cavabı.
Mobil gözləyir: { "access", "refresh" } (SimpleJWT).
"""

from secrets import token_urlsafe

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import EmailLoginSerializer, GoogleAuthSerializer, RegisterSerializer

User = get_user_model()


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register(request):
    ser = RegisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user = ser.save()
    return Response(_tokens_for_user(user), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login(request):
    ser = EmailLoginSerializer(data=request.data, context={"request": request})
    ser.is_valid(raise_exception=True)
    user = ser.validated_data["user"]
    return Response(_tokens_for_user(user))


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def google_auth(request):
    """
    POST { "id_token": "..." } — Google JWT yoxlanır, istifadəçi tapılır/yaradılır.
    Tələb: google-auth paketi və GOOGLE_OAUTH_CLIENT_ID (Web client id).
    """
    ser = GoogleAuthSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    token = ser.validated_data["id_token"]

    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
    except ImportError:
        return Response(
            {"detail": "Serverdə google-auth quraşdırılmayıb."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )

    client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", None) or getattr(
        settings, "EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID", ""
    )
    if not client_id:
        return Response(
            {"detail": "GOOGLE_OAUTH_CLIENT_ID təyin edilməyib (settings)."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        idinfo = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), client_id
        )
    except ValueError as e:
        return Response(
            {"detail": f"Google token etibarsızdır: {e}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    email = (idinfo.get("email") or "").lower().strip()
    if not email:
        return Response(
            {"detail": "Google cavabında email yoxdur."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        user = User.objects.create_user(
            username=email,
            email=email,
            password=token_urlsafe(32),
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])

    return Response(_tokens_for_user(user))


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    u = request.user
    return Response(
        {
            "id": u.pk,
            "email": getattr(u, "email", "") or "",
            "username": u.username,
        }
    )
