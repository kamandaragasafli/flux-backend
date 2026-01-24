"""
Database Router
Hangi model'in hangi database'i kullanacağını belirler
"""
from django.conf import settings


class ExternalDatabaseRouter:
    """
    External database router
    External model'leri 'external' database'e yönlendirir
    """
    
    # External database kullanacak app'ler
    external_apps = ['external']  # Eğer external app oluşturursanız
    
    # External database kullanacak model'ler (app_name.ModelName formatında)
    external_models = [
        'tracking.SolveyRegion',
        'tracking.SolveyCity',
        'tracking.SolveyHospital',
        'tracking.SolveyDoctor',
    ]
    
    def db_for_read(self, model, **hints):
        """Read işlemleri için hangi database kullanılacak"""
        if model._meta.app_label in self.external_apps:
            return 'external'
        if f"{model._meta.app_label}.{model.__name__}" in self.external_models:
            return 'external'
        return None  # Default database kullan
    
    def db_for_write(self, model, **hints):
        """Write işlemleri için hangi database kullanılacak"""
        if model._meta.app_label in self.external_apps:
            return 'external'
        if f"{model._meta.app_label}.{model.__name__}" in self.external_models:
            return 'external'
        return None  # Default database kullan
    
    def allow_relation(self, obj1, obj2, **hints):
        """İki model arasında relation'a izin ver"""
        # İki model de aynı database'deyse relation'a izin ver
        db_set = {'default', 'external'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Migration'lara izin ver"""
        if db == 'external':
            # External database'e sadece external app'ler migrate edilebilir
            return app_label in self.external_apps
        elif app_label in self.external_apps:
            # External app'ler default database'e migrate edilemez
            return False
        return None  # Diğer durumlar için default davranış

