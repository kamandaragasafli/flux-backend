# Fitlog mobil — backend auth modulu

Bu qovluq **Solvey Pharma** Django layihəsinə **kopyalanıb** birləşdirilmə üçündür. Burada tam Django layihəsi yoxdur; yalnız **`fitlog_auth`** tətbiqi və qoşma təlimatı var.

## URL-lər (mobil `EXPO_PUBLIC_API_BASE_URL=https://app.solveypharma.com.az/api` olduqda)

| Metod | Path | Təsvir |
|--------|------|--------|
| POST | `/api/auth/register/` | `{"email","password"}` → `201` + JWT |
| POST | `/api/auth/login/` | `{"email","password"}` → `200` + JWT |
| POST | `/api/auth/google/` | `{"id_token"}` → `200` + JWT |
| GET | `/api/auth/me/` | `Authorization: Bearer <access>` → istifadəçi |

Cavab formatı: `{"access": "...", "refresh": "..."}` (djangorestframework-simplejwt).

## Quraşdırma

1. **`fitlog_auth`** qovluğunu öz Django layihənizin kökünə kopyalayın ( `manage.py` ilə eyni səviyyədə olan `apps/` və ya birbaşa `fitlog_auth/`).

2. **`settings.py`**:
   ```python
   INSTALLED_APPS = [
       # ...
       "rest_framework",
       "rest_framework_simplejwt",
       "fitlog_auth",
   ]

   REST_FRAMEWORK = {
       "DEFAULT_AUTHENTICATION_CLASSES": (
           "rest_framework_simplejwt.authentication.JWTAuthentication",
           # mövcud session auth və s. saxlaya bilərsiniz
       ),
   }

   from datetime import timedelta
   SIMPLE_JWT = {
       "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
       "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
   }

   # Google mobil girişi üçün (Web client id — Google Cloud)
   GOOGLE_OAUTH_CLIENT_ID = "....apps.googleusercontent.com"
   ```

3. **Əsas `urls.py`** — `api/` prefiksi altında (sizdə artıq `DefaultRouter` varsa eyni `api/` include-a əlavə edin):

   ```python
   urlpatterns = [
       path("api/", include("fitlog_auth.urls")),
       # mövcud: path("api/", include(router.urls)),
   ]
   ```

   **Diqqət:** Əgər `api/` üçün yalnız bir `include` istifadə edirsinizsə, `urlpatterns`-ə **hər iki** `include`-u eyni `api/` prefiksi ilə əlavə etmək olar — Django üst-üstə düşən path-ləri birləşdirir.

4. **Paketlər:**
   ```bash
   pip install djangorestframework djangorestframework-simplejwt google-auth
   ```
   (`requirements-fitlog_auth.txt` istinad üçündür.)

5. **CORS** (Expo mobil üçün) — `django-cors-headers` ilə brauzer/mobil origin-ləri icazə verin.

6. **İstifadəçi modeli:** Standart `User` — qeydiyyatda `username=email` yazılır. Öz `AbstractUser` istifadə edirsinizsə, `views.py` / `serializers.py`-də uyğunlaşdırın.

7. **Migrasiya:** Yeni model əlavə olunmayıb; mövcud `auth_user` cədvəli istifadə olunur.

## Təhlükəsizlik

- Prod-da `DEBUG=False`, HTTPS, rate limit, parol siyasəti.
- Google üçün yalnız etibarlı `id_token` qəbul edilir.

## Mobil layihə

`mobile/.env` içində `EXPO_PUBLIC_API_BASE_URL` və lazım olsa `EXPO_PUBLIC_API_*_PATH` dəyərləri bu path-lərlə üst-üstə düşməlidir (default artıq `auth/login/` və s.).

## Windows: `runserver` — WinError 10013

1. **Port məşğuldur:** `8000` / `8001` üçün köhnə `python.exe` (runserver) işləyir — Tapşırıq Menecerində sonlandırın və ya boş port seçin, məs.: `py manage.py runserver 127.0.0.1:9000`.
2. **StatReloader:** Bəzən avtomatik yenidən yükləmə əlavə socket açır və 10013 verir. Sınaq:  
   `py manage.py runserver 127.0.0.1:9000 --noreload`
3. Antivirus / firewall müvəqqəti söndürüb yenidən yoxlayın.
