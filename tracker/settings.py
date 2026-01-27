import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me-in-production")

DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"

# Server IP ve localhost için allowed hosts (Expo Go için)
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "206.189.53.174,localhost,127.0.0.1").split(",")
CSRF_TRUSTED_ORIGINS = [
    "http://206.189.53.174",
    "https://206.189.53.174",
    "http://206.189.53.174:8081",
    "https://206.189.53.174:8081",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "tracking",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Static files serving
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tracker.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tracker.wsgi.application"


# Database configuration
# USE_SQLITE=true for local development, USE_SQLITE=false for production (PostgreSQL)
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    # SQLite configuration (local development)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    # PostgreSQL configuration (production/server)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "flux_tracker"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "OPTIONS": {
                "connect_timeout": 10,
            },
        }
    }

# External Database Configuration (İkinci database - isteğe bağlı)
# Eğer external database kullanmak istiyorsanız, .env dosyasına ekleyin:
# USE_EXTERNAL_DB=true
# EXTERNAL_DB_NAME=external_db_name
# EXTERNAL_DB_USER=external_user
# EXTERNAL_DB_PASSWORD=external_password
# EXTERNAL_DB_HOST=external_host
# EXTERNAL_DB_PORT=5432
USE_EXTERNAL_DB = os.getenv("USE_EXTERNAL_DB", "false").lower() == "true"

if USE_EXTERNAL_DB:
    DATABASES["external"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("EXTERNAL_DB_NAME", ""),
        "USER": os.getenv("EXTERNAL_DB_USER", ""),
        "PASSWORD": os.getenv("EXTERNAL_DB_PASSWORD", ""),
        "HOST": os.getenv("EXTERNAL_DB_HOST", ""),
        "PORT": os.getenv("EXTERNAL_DB_PORT", "5432"),
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }

# Database Router (hangi model hangi database'i kullanacak)
DATABASE_ROUTERS = ['tracking.db_router.ExternalDatabaseRouter']

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "az"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # Dashboard için session auth
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CORS ayarları
# Expo Go için tüm origin'lere izin ver (Expo Go farklı IP'lerden bağlanabilir)
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "true").lower() == "true"

# Eğer CORS_ALLOW_ALL_ORIGINS false ise, spesifik origin'ler ekleyin
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8081",
    "http://localhost:8082",
    "http://localhost:19006",
    "http://127.0.0.1:8081",
    "http://127.0.0.1:8082",
    "http://127.0.0.1:19006",
    "exp://localhost:8081",  # Expo Go
    "exp://192.168.1.100:8081",  # Expo Go local network
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "false").lower() == "true"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# WhiteNoise settings for static files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

