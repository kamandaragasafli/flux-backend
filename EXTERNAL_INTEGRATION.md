# External System Integration Guide

Bu dokümantasyon, başka bir sistemden (domain/IP veya database) veri çekmek için kullanılır.

## İki Yöntem

### Yöntem 1: API'den Veri Çekme (Domain/IP)

External sisteminiz bir API sunuyorsa, bu yöntemi kullanabilirsiniz.

#### Kurulum

1. `.env` dosyasına ekleyin:
```env
EXTERNAL_API_URL=http://your-external-api.com
# veya IP ile:
EXTERNAL_API_URL=http://192.168.1.100:8000

# Eğer API key gerekiyorsa:
EXTERNAL_API_KEY=your-api-key
```

2. API endpoint'lerini `external_service.py` dosyasında özelleştirin:
```python
def fetch_users(self) -> List[Dict]:
    data = self.get('/api/users/')  # Kendi endpoint'inizi yazın
    return data.get('results', data)
```

#### Kullanım

```python
from tracking.external_service import get_external_api_service

api_service = get_external_api_service()
users = api_service.fetch_users()
orders = api_service.fetch_orders(user_id=123)
```

#### API Endpoint'leri

- `GET /api/external/users/?use_api=true` - API'den kullanıcıları çek
- `GET /api/external/orders/?use_api=true&user_id=123` - API'den siparişleri çek

---

### Yöntem 2: İkinci Database'den Veri Çekme

External sisteminizin database'ine direkt bağlanmak istiyorsanız, bu yöntemi kullanın.

#### Kurulum

1. `.env` dosyasına ekleyin:
```env
USE_EXTERNAL_DB=true
EXTERNAL_DB_NAME=external_database_name
EXTERNAL_DB_USER=external_user
EXTERNAL_DB_PASSWORD=external_password
EXTERNAL_DB_HOST=external_host_or_ip
EXTERNAL_DB_PORT=5432
```

2. `settings.py` otomatik olarak ikinci database'i yapılandıracak.

3. Database router'ı `db_router.py` dosyasında özelleştirin (hangi model'ler external DB kullanacak).

#### Kullanım

```python
from tracking.external_service import get_external_db_service

db_service = get_external_db_service()
users = db_service.get_users()
orders = db_service.get_orders(user_id=123)

# Özel tablo sorgusu
products = db_service.get_custom_data('products', {'category': 'electronics'})
```

#### API Endpoint'leri

- `GET /api/external/users/?use_api=false` - Database'den kullanıcıları çek
- `GET /api/external/orders/?use_api=false&user_id=123` - Database'den siparişleri çek
- `GET /api/external/custom/?table=products&category=electronics` - Özel tablo sorgusu

---

## Örnek Kullanım Senaryoları

### Senaryo 1: E-ticaret Sistemi ile Entegrasyon

```python
# External e-ticaret sisteminden siparişleri çek
from tracking.external_service import get_external_api_service

api_service = get_external_api_service()
orders = api_service.fetch_orders()

# Her sipariş için tracking route oluştur
for order in orders:
    # Sipariş takibi için route başlat
    # ...
```

### Senaryo 2: CRM Sistemi ile Entegrasyon

```python
# External CRM'den müşteri bilgilerini çek
from tracking.external_service import get_external_db_service

db_service = get_external_db_service()
customers = db_service.get_custom_data('customers', {'status': 'active'})
```

---

## İki Database Birlikte Çalışabilir mi?

**Evet!** Django'da birden fazla database kullanabilirsiniz:

1. **Default Database**: Mevcut Flux Tracker verileri (routes, locations, users)
2. **External Database**: External sistemin verileri

### Avantajlar:
- ✅ İki sistem birbirinden bağımsız çalışır
- ✅ Her database kendi migration'larını yönetir
- ✅ Database router ile hangi model'in hangi DB'yi kullanacağını belirleyebilirsiniz
- ✅ Transaction'lar ayrı ayrı yönetilir

### Dikkat Edilmesi Gerekenler:
- ⚠️ İki database arasında ForeignKey kullanılamaz (farklı database'ler)
- ⚠️ Join işlemleri yapılamaz (farklı database'ler)
- ⚠️ Her database için ayrı connection pool kullanılır

---

## Test Etme

### 1. API Yöntemi Testi

```bash
# Terminal'den test
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/external/users/?use_api=true
```

### 2. Database Yöntemi Testi

```bash
# Django shell'de test
python manage.py shell

>>> from tracking.external_service import get_external_db_service
>>> db_service = get_external_db_service()
>>> users = db_service.get_users()
>>> print(users)
```

---

## Güvenlik Notları

1. **API Key**: External API'ye erişim için API key kullanın
2. **Database Credentials**: `.env` dosyasını asla commit etmeyin
3. **HTTPS**: Production'da mutlaka HTTPS kullanın
4. **Rate Limiting**: External API'ye çok fazla request göndermeyin
5. **Error Handling**: Her zaman try-except kullanın

---

## Sorun Giderme

### "Connection refused" Hatası
- External database/API'nin erişilebilir olduğundan emin olun
- Firewall ayarlarını kontrol edin
- Host ve port bilgilerini doğrulayın

### "Authentication failed" Hatası
- Database kullanıcı adı ve şifresini kontrol edin
- API key'in doğru olduğundan emin olun

### "Table does not exist" Hatası
- Tablo adını doğrulayın
- Database'de tablonun var olduğundan emin olun

