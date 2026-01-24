"""
External Service Integration
İki yöntem desteklenir:
1. API'den veri çekme (Domain/IP ile)
2. İkinci database'den veri çekme
"""
import requests
import os
from django.db import connections
from django.conf import settings
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ExternalAPIService:
    """External API'den veri çekme servisi"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 10):
        """
        Args:
            base_url: External API'nin base URL'i (örn: https://api.example.com veya http://192.168.1.100:8000)
            api_key: API key (gerekirse)
            timeout: Request timeout (saniye)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """GET request yap"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"[EXTERNAL_API] Error fetching {url}: {e}")
            raise
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """POST request yap"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"[EXTERNAL_API] Error posting to {url}: {e}")
            raise
    
    def fetch_users(self) -> List[Dict]:
        """External sistemden kullanıcıları çek"""
        try:
            data = self.get('/api/users/')  # Endpoint'i kendi API'nize göre değiştirin
            return data.get('results', data) if isinstance(data, dict) else data
        except Exception as e:
            logger.error(f"[EXTERNAL_API] Error fetching users: {e}")
            return []
    
    def fetch_orders(self, user_id: Optional[int] = None) -> List[Dict]:
        """External sistemden siparişleri çek"""
        try:
            params = {'user_id': user_id} if user_id else {}
            data = self.get('/api/orders/', params=params)
            return data.get('results', data) if isinstance(data, dict) else data
        except Exception as e:
            logger.error(f"[EXTERNAL_API] Error fetching orders: {e}")
            return []
    
    def fetch_doctors(self) -> List[Dict]:
        """Solvey sistemden doktor listesini çek"""
        try:
            data = self.get('/doctors/list/')
            return data.get('results', data) if isinstance(data, dict) else data
        except Exception as e:
            logger.error(f"[EXTERNAL_API] Error fetching doctors: {e}")
            return []
    
    def fetch_regions_areas(self) -> List[Dict]:
        """Solvey sistemden bölge alanlarını çek"""
        try:
            data = self.get('/regions/area/')
            return data.get('results', data) if isinstance(data, dict) else data
        except Exception as e:
            logger.error(f"[EXTERNAL_API] Error fetching regions areas: {e}")
            return []
    
    def fetch_hospitals(self) -> List[Dict]:
        """Solvey sistemden hastane listesini çek"""
        try:
            data = self.get('/regions/hospital/')
            return data.get('results', data) if isinstance(data, dict) else data
        except Exception as e:
            logger.error(f"[EXTERNAL_API] Error fetching hospitals: {e}")
            return []


class ExternalDatabaseService:
    """İkinci database'den veri çekme servisi"""
    
    def __init__(self, db_alias: str = 'external'):
        """
        Args:
            db_alias: settings.py'de tanımlı database alias'ı
        """
        self.db_alias = db_alias
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Raw SQL query çalıştır"""
        try:
            with connections[self.db_alias].cursor() as cursor:
                cursor.execute(query, params or ())
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[EXTERNAL_DB] Error executing query: {e}")
            return []
    
    def get_users(self) -> List[Dict]:
        """Solvey database'den kullanıcıları çek"""
        # Solvey database'deki kullanıcı tablosunu sorgula
        # Tablo adını database'e göre ayarlayın
        query = """
            SELECT id, username, email, first_name, last_name, is_active, date_joined 
            FROM auth_user 
            ORDER BY date_joined DESC
        """
        return self.execute_query(query)
    
    def get_orders(self, user_id: Optional[int] = None) -> List[Dict]:
        """Solvey database'den siparişleri çek"""
        # Solvey database'deki sipariş tablosunu sorgula
        # Tablo adını database'e göre ayarlayın
        if user_id:
            query = "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC"
            return self.execute_query(query, (user_id,))
        else:
            query = "SELECT * FROM orders ORDER BY created_at DESC LIMIT 100"
            return self.execute_query(query)
    
    def get_doctors(self) -> List[Dict]:
        """Solvey database'den doktor listesini çek (Doctors modeli)"""
        # Tablo adını environment variable'dan al, yoksa default kullan
        doctors_table = os.getenv('SOLVEY_DOCTORS_TABLE', 'tracking_doctors')
        region_table = os.getenv('SOLVEY_REGIONS_AREA_TABLE', 'tracking_region')
        city_table = os.getenv('SOLVEY_CITY_TABLE', 'tracking_city')
        hospital_table = os.getenv('SOLVEY_REGIONS_HOSPITAL_TABLE', 'tracking_hospital')
        order_by = os.getenv('SOLVEY_DOCTORS_ORDER_BY', 'ad')
        
        # Doctors modeline göre sorgu (ForeignKey'leri JOIN ile çek)
        query = f"""
            SELECT 
                d.id,
                d.ad,
                d.ixtisas,
                d.kategoriya,
                d.derece,
                d.cinsiyyet,
                d.number,
                d.barkod,
                d.razılaşma,
                d.previous_debt,
                d.hesablanan_miqdar,
                d.hekimden_silinen,
                d.datasiya,
                d.borc,
                d.yekun_borc,
                d.created_at,
                d.bolge_id,
                d.city_id,
                d.klinika_id,
                r.region_name as bolge_name,
                r.region_type as bolge_type,
                c.city_name,
                h.hospital_name as klinika_name
            FROM "{doctors_table}" d
            LEFT JOIN "{region_table}" r ON d.bolge_id = r.id
            LEFT JOIN "{city_table}" c ON d.city_id = c.id
            LEFT JOIN "{hospital_table}" h ON d.klinika_id = h.id
            ORDER BY d.{order_by} ASC
        """
        return self.execute_query(query)
    
    def get_regions_areas(self) -> List[Dict]:
        """Solvey database'den bölge alanlarını çek (Region modeli)"""
        # Tablo adını environment variable'dan al, yoksa default kullan
        table_name = os.getenv('SOLVEY_REGIONS_AREA_TABLE', 'tracking_region')
        order_by = os.getenv('SOLVEY_REGIONS_AREA_ORDER_BY', 'region_name')
        
        # Region modeline göre sorgu
        query = f"""
            SELECT 
                id,
                region_name,
                region_type
            FROM "{table_name}" 
            ORDER BY {order_by} ASC
        """
        return self.execute_query(query)
    
    def get_hospitals(self) -> List[Dict]:
        """Solvey database'den hastane listesini çek (Hospital modeli)"""
        # Tablo adını environment variable'dan al, yoksa default kullan
        hospital_table = os.getenv('SOLVEY_REGIONS_HOSPITAL_TABLE', 'tracking_hospital')
        region_table = os.getenv('SOLVEY_REGIONS_AREA_TABLE', 'tracking_region')
        city_table = os.getenv('SOLVEY_CITY_TABLE', 'tracking_city')
        order_by = os.getenv('SOLVEY_HOSPITALS_ORDER_BY', 'hospital_name')
        
        # Hospital modeline göre sorgu (ForeignKey'leri JOIN ile çek)
        query = f"""
            SELECT 
                h.id,
                h.hospital_name,
                h.region_net_id,
                h.city_id,
                r.region_name,
                r.region_type,
                c.city_name
            FROM "{hospital_table}" h
            LEFT JOIN "{region_table}" r ON h.region_net_id = r.id
            LEFT JOIN "{city_table}" c ON h.city_id = c.id
            ORDER BY h.{order_by} ASC
        """
        return self.execute_query(query)
    
    def get_cities(self, region_id: Optional[int] = None) -> List[Dict]:
        """Solvey database'den şehir listesini çek (City modeli)"""
        city_table = os.getenv('SOLVEY_CITY_TABLE', 'tracking_city')
        region_table = os.getenv('SOLVEY_REGIONS_AREA_TABLE', 'tracking_region')
        order_by = os.getenv('SOLVEY_CITY_ORDER_BY', 'city_name')
        
        if region_id:
            # Belirli bir bölgeye ait şehirler
            query = f"""
                SELECT 
                    c.id,
                    c.region_id,
                    c.city_name,
                    r.region_name,
                    r.region_type
                FROM "{city_table}" c
                LEFT JOIN "{region_table}" r ON c.region_id = r.id
                WHERE c.region_id = %s
                ORDER BY c.{order_by} ASC
            """
            return self.execute_query(query, (region_id,))
        else:
            # Tüm şehirler
            query = f"""
                SELECT 
                    c.id,
                    c.region_id,
                    c.city_name,
                    r.region_name,
                    r.region_type
                FROM "{city_table}" c
                LEFT JOIN "{region_table}" r ON c.region_id = r.id
                ORDER BY c.{order_by} ASC
            """
            return self.execute_query(query)
    
    def get_tables(self) -> List[str]:
        """Database'deki tüm tabloları listele"""
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """
        result = self.execute_query(query)
        return [row['table_name'] for row in result]
    
    def get_table_columns(self, table_name: str) -> List[Dict]:
        """Bir tablonun kolonlarını listele"""
        query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """
        return self.execute_query(query, (table_name,))
    
    def get_custom_data(self, table_name: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Herhangi bir tablodan veri çek"""
        query = f"SELECT * FROM {table_name}"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = %s")
                params.append(value)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        return self.execute_query(query, tuple(params) if params else None)


# Singleton instance'lar (isteğe bağlı)
_external_api_service: Optional[ExternalAPIService] = None
_external_db_service: Optional[ExternalDatabaseService] = None


def get_external_api_service() -> ExternalAPIService:
    """External API service instance'ını al"""
    global _external_api_service
    if _external_api_service is None:
        base_url = os.getenv('EXTERNAL_API_URL', '')
        api_key = os.getenv('EXTERNAL_API_KEY', '')
        _external_api_service = ExternalAPIService(base_url, api_key)
    return _external_api_service


def get_external_db_service() -> ExternalDatabaseService:
    """External database service instance'ını al"""
    global _external_db_service
    if _external_db_service is None:
        _external_db_service = ExternalDatabaseService()
    return _external_db_service

