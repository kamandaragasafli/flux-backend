from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Bu email artıq qeydiyyatdan keçib.")
        return value.lower().strip()

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
        )
        return user


class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email", "").lower().strip()
        password = attrs.get("password")
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )
        if user is None and User.objects.filter(email__iexact=email).exists():
            user = authenticate(
                request=self.context.get("request"),
                username=User.objects.get(email__iexact=email).username,
                password=password,
            )
        if user is None:
            raise serializers.ValidationError(
                {"detail": "Invalid login credentials"},
                code="authorization",
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {"detail": "Hesab deaktivdir."},
                code="authorization",
            )
        attrs["user"] = user
        return attrs


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True)
