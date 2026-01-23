# Backend Deployment Guide

Bu rehber, Django backend'inizi PostgreSQL veritabanı ile production ortamına deploy etmek için hazırlanmıştır.

## Database Yapılandırması

Backend, environment variable ile SQLite veya PostgreSQL arasında seçim yapabilir:

- **Local Development:** `USE_SQLITE=true` (SQLite kullanır)
- **Server/Production:** `USE_SQLITE=false` (PostgreSQL kullanır)

## Manuel Deployment

### 1. PostgreSQL Kurulumu

```bash
# Ubuntu/Debian için
sudo apt update
sudo apt install postgresql postgresql-contrib

# PostgreSQL'e bağlan
sudo -u postgres psql

# Veritabanı ve kullanıcı oluştur
CREATE DATABASE flux_tracker;
CREATE USER flux_user WITH PASSWORD 'your-secure-password';
ALTER ROLE flux_user SET client_encoding TO 'utf8';
ALTER ROLE flux_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE flux_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE flux_tracker TO flux_user;
\q
```

### 2. Backend Sunucuya Deploy

```bash
# Sunucuya bağlan
ssh user@your-server.com

# Projeyi klonla veya yükle
cd /var/www/flux-tracker/backend

# Python virtual environment oluştur
python3 -m venv venv
source venv/bin/activate

# Gerekli paketleri yükle
pip install -r requirements.txt

# .env dosyası oluştur ve düzenle
nano .env

# Database migrate
python manage.py migrate

# Superuser oluştur
python manage.py createsuperuser

# Static dosyaları topla
python manage.py collectstatic --noinput

# Gunicorn ile çalıştır (production için)
gunicorn tracker.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### 2. CORS Ayarları (settings.py)

Production için CORS ayarlarını güncelleyin:

```python
# Production için
CORS_ALLOW_ALL_ORIGINS = False  # Güvenlik için False yapın

CORS_ALLOWED_ORIGINS = [
    "https://your-expo-app.com",
    "exp://your-expo-url",
    # Expo Go için gerekli origin'leri ekleyin
]

# Veya development için
CORS_ALLOW_ALL_ORIGINS = True  # Sadece development için
```

### 3. Mobil Uygulamada API URL Güncelleme

`mobile/config/api.ts` dosyasında:

```typescript
const PRODUCTION_API_URL = 'https://your-server.com';
```

veya `mobile/app.json` dosyasında:

```json
{
  "extra": {
    "apiBaseUrl": "https://your-server.com"
  }
}
```

### 4. Expo Go'da Test

1. Expo Go uygulamasını telefonunuza indirin
2. `npx expo start` komutunu çalıştırın
3. QR kodu Expo Go ile tarayın
4. Uygulama backend'e bağlanacak

### 5. HTTPS Kullanımı

**ÖNEMLİ:** Production'da mutlaka HTTPS kullanın!

- iOS ve Android modern versiyonları HTTP'ye izin vermez
- SSL sertifikası gerekli (Let's Encrypt ücretsiz)

### 6. Firewall Ayarları

Sunucuda port 8000'in açık olduğundan emin olun:

```bash
# UFW kullanıyorsanız
sudo ufw allow 8000/tcp

# Veya iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

### 7. Nginx Reverse Proxy (Önerilen)

```nginx
server {
    listen 80;
    server_name your-server.com;

    # Static files için (opsiyonel - WhiteNoise de kullanılabilir)
    location /static/ {
        alias /var/www/flux-tracker/backend/staticfiles/;
    }

    location /media/ {
        alias /var/www/flux-tracker/backend/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}

# HTTPS için (Let's Encrypt ile)
server {
    listen 443 ssl http2;
    server_name your-server.com;

    ssl_certificate /etc/letsencrypt/live/your-server.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-server.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Systemd Service (Gunicorn için)

`/etc/systemd/system/flux-tracker.service` dosyası oluşturun:

```ini
[Unit]
Description=Flux Tracker Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/flux-tracker/backend
Environment="PATH=/var/www/flux-tracker/backend/venv/bin"
ExecStart=/var/www/flux-tracker/backend/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    tracker.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Service'i başlat
sudo systemctl start flux-tracker
sudo systemctl enable flux-tracker

# Durumu kontrol et
sudo systemctl status flux-tracker
```

### 8. Environment Variables

Production için `backend/.env` dosyası oluşturun:

```env
# Django Settings
DJANGO_SECRET_KEY=your-very-secure-secret-key-here
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database Configuration
# Local için: USE_SQLITE=true
# Server için: USE_SQLITE=false (PostgreSQL kullanır)
USE_SQLITE=false

# PostgreSQL ayarları (USE_SQLITE=false olduğunda gerekli)
DB_NAME=flux_tracker
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432

# CORS Settings
CORS_ALLOW_ALL_ORIGINS=false

# Security Settings
SECURE_SSL_REDIRECT=true
```

**Güvenlik İpuçları:**
- `DJANGO_SECRET_KEY` için güçlü bir key oluşturun: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
- `.env` dosyasını asla git'e commit etmeyin
- Production'da `DJANGO_DEBUG=false` olmalı
- **Server'da mutlaka `USE_SQLITE=false` yapın!**

### 9. PostgreSQL Database Konfigürasyonu

Server'da `.env` dosyasında `USE_SQLITE=false` yapın ve PostgreSQL ayarlarını ekleyin:

```env
USE_SQLITE=false
DB_NAME=flux_tracker
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432
```

**Önemli:**
- **Local development:** `USE_SQLITE=true` (SQLite kullanır, hızlı başlangıç için)
- **Server/Production:** `USE_SQLITE=false` (PostgreSQL kullanır, production için gerekli)

#### PostgreSQL Bağlantı Testi

```bash
# PostgreSQL'in çalıştığını kontrol et
sudo systemctl status postgresql

# Veritabanına bağlan
psql -U postgres -d flux_tracker

# Tabloları kontrol et
\dt
```

#### Migration İşlemleri

```bash
# Migration'ları oluştur (model değişikliklerinden sonra)
python manage.py makemigrations

# Migration'ları uygula
python manage.py migrate

# Migration durumunu kontrol et
python manage.py showmigrations
```

### 10. Static Files

Static dosyalar WhiteNoise ile otomatik olarak serve edilir. Production'da:

```bash
# Static dosyaları topla
python manage.py collectstatic --noinput
```

WhiteNoise ayarları `settings.py`'de zaten yapılandırılmıştır. Nginx kullanıyorsanız, static dosyalar için Nginx'i de kullanabilirsiniz.

## Expo Go ile Çalıştırma

Backend'i sunucuya deploy ettikten sonra Expo Go'da çalıştırmak için:

### Mobil Uygulamada API URL Güncelleme

`mobile/config/api.ts` dosyasında:

```typescript
const PRODUCTION_API_URL = 'https://your-server.com';
```

veya `mobile/app.json` dosyasında:

```json
{
  "extra": {
    "apiBaseUrl": "https://your-server.com"
  }
}
```

### Expo Go'da Test

1. Expo Go uygulamasını telefonunuza indirin
2. `npx expo start` komutunu çalıştırın
3. QR kodu Expo Go ile tarayın
4. Uygulama backend'e bağlanacak

## Expo Go Bağlantı Sorunları

### Sorun: "Network request failed"

**Çözüm:**
1. Backend URL'inin doğru olduğundan emin olun
2. HTTPS kullanıyorsanız sertifika geçerli olmalı
3. CORS ayarlarını kontrol edin
4. Firewall'u kontrol edin

### Sorun: "CORS error"

**Çözüm:**
```python
# settings.py
CORS_ALLOW_ALL_ORIGINS = True  # Development için
# veya
CORS_ALLOWED_ORIGINS = [
    "exp://192.168.1.100:8081",  # Expo Go URL'iniz
]
```

### Sorun: "Connection timeout"

**Çözüm:**
1. Sunucunun çalıştığından emin olun
2. Port'un açık olduğunu kontrol edin
3. IP adresinin doğru olduğunu kontrol edin

## Test Etme

```bash
# Backend'i test et
curl https://your-server.com/api/auth/login/ -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# CORS'u test et
curl -H "Origin: exp://192.168.1.100:8081" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS \
  https://your-server.com/api/auth/login/
```

## Güvenlik Notları

1. ✅ Production'da `DEBUG = False`
2. ✅ `SECRET_KEY` environment variable olarak saklayın
3. ✅ HTTPS kullanın
4. ✅ CORS'u sınırlayın (`CORS_ALLOW_ALL_ORIGINS=false`)
5. ✅ PostgreSQL güvenli şifre kullanın
6. ✅ `.env` dosyasını git'e commit etmeyin
7. ✅ Rate limiting ekleyin (django-ratelimit paketi)
8. ✅ SQL injection koruması (Django otomatik)
9. ✅ XSS koruması (Django otomatik)
10. ✅ CSRF koruması aktif
11. ✅ WhiteNoise ile static dosya güvenliği

## Backup ve Restore

### PostgreSQL Backup

```bash
# Backup oluştur
pg_dump -U postgres flux_tracker > backup_$(date +%Y%m%d).sql

# Backup'tan restore
psql -U postgres flux_tracker < backup_20240101.sql
```


## Troubleshooting

### PostgreSQL Bağlantı Hatası

```bash
# PostgreSQL servisinin çalıştığını kontrol et
sudo systemctl status postgresql

# PostgreSQL loglarını kontrol et
sudo tail -f /var/log/postgresql/postgresql-*.log

# Bağlantıyı test et
psql -U postgres -h localhost -d flux_tracker
```

### Migration Hataları

```bash
# Migration durumunu kontrol et
python manage.py showmigrations

# Fake migration (veritabanı zaten güncel ise)
python manage.py migrate --fake

# Migration'ı geri al
python manage.py migrate app_name migration_number
```

### Static Files Sorunları

```bash
# Static dosyaları temizle ve yeniden topla
rm -rf staticfiles/
python manage.py collectstatic --noinput --clear
```

## Production Checklist

- [ ] PostgreSQL kurulu ve çalışıyor
- [ ] `.env` dosyası oluşturuldu ve güvenli değerlerle dolduruldu
- [ ] `DJANGO_SECRET_KEY` güçlü bir key ile değiştirildi
- [ ] `DJANGO_DEBUG=false` ayarlandı
- [ ] `ALLOWED_HOSTS` doğru domain'lerle ayarlandı
- [ ] `CORS_ALLOW_ALL_ORIGINS=false` (production için)
- [ ] Migration'lar uygulandı
- [ ] Static dosyalar toplandı (`collectstatic`)
- [ ] Superuser oluşturuldu
- [ ] Gunicorn systemd service olarak kuruldu
- [ ] Nginx reverse proxy yapılandırıldı
- [ ] HTTPS/SSL sertifikası kuruldu
- [ ] Firewall ayarları yapıldı
- [ ] Backup stratejisi belirlendi
- [ ] Log monitoring kuruldu

