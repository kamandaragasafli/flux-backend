# Flux Tracker Backend

Django REST Framework ile geliştirilmiş GPS tracking backend uygulaması.

## Özellikler

- PostgreSQL ve SQLite veritabanı desteği
- JWT Authentication
- RESTful API
- CORS desteği
- Production-ready yapılandırma

## Hızlı Başlangıç

### Gereksinimler

- Python 3.11+
- PostgreSQL 12+
- pip

### Kurulum

1. **Virtual environment oluştur:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Bağımlılıkları yükle:**
```bash
pip install -r requirements.txt
```

3. **Environment variables ayarla:**
```bash
cp env.example .env
# .env dosyasını düzenle
# Local için: USE_SQLITE=true
# Server için: USE_SQLITE=false ve PostgreSQL ayarlarını ekle
```

4. **PostgreSQL veritabanı oluştur (sadece server için gerekli):**
```bash
# Eğer USE_SQLITE=false kullanıyorsanız:
sudo -u postgres psql
CREATE DATABASE flux_tracker;
CREATE USER flux_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE flux_tracker TO flux_user;
\q
```

5. **Migration'ları çalıştır:**
```bash
python manage.py migrate
```

6. **Superuser oluştur:**
```bash
python manage.py createsuperuser
```

7. **Development server'ı başlat:**
```bash
python manage.py runserver
```

## Database Yapılandırması

Backend, environment variable ile SQLite veya PostgreSQL arasında seçim yapabilir:

**Local Development (.env dosyasında):**
```env
USE_SQLITE=true
```

**Server/Production (.env dosyasında):**
```env
USE_SQLITE=false
DB_NAME=flux_tracker
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

## Production Deployment

Detaylı deployment rehberi için [DEPLOY.md](DEPLOY.md) dosyasına bakın.

## API Endpoints

- `/api/auth/login/` - Kullanıcı girişi
- `/api/auth/register/` - Kullanıcı kaydı
- `/api/routes/` - Route yönetimi
- `/api/locations/` - Lokasyon takibi

## Veritabanı

- **Local Development:** `USE_SQLITE=true` ile SQLite kullanılır (hızlı başlangıç)
- **Server/Production:** `USE_SQLITE=false` ile PostgreSQL kullanılır (production için gerekli)

## Güvenlik

- Production'da `DEBUG=False` olmalı
- `SECRET_KEY` environment variable olarak saklanmalı
- `.env` dosyası git'e commit edilmemeli
- HTTPS kullanılmalı
- CORS ayarları production için sınırlandırılmalı

## Lisans

Bu proje özel bir projedir.

