"""
Solvey Database Models
Bu modellər external (Solvey) database-dən məlumat çəkir
"""
from django.db import models


class SolveyRegion(models.Model):
    """Solvey regions_region cədvəli"""
    id = models.IntegerField(primary_key=True)
    region_name = models.CharField(max_length=255)
    region_type = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'regions_region'
        managed = False  # Django migration etməsin
        app_label = 'tracking'
    
    def __str__(self):
        return self.region_name


class SolveyCity(models.Model):
    """Solvey regions_city cədvəli"""
    id = models.IntegerField(primary_key=True)
    city_name = models.CharField(max_length=255)
    region_id = models.IntegerField()
    
    class Meta:
        db_table = 'regions_city'
        managed = False
        app_label = 'tracking'
    
    def __str__(self):
        return self.city_name


class SolveyHospital(models.Model):
    """Solvey regions_hospital cədvəli"""
    id = models.IntegerField(primary_key=True)
    hospital_name = models.CharField(max_length=255)
    city_id = models.IntegerField(null=True, blank=True)
    region_net_id = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'regions_hospital'
        managed = False
        app_label = 'tracking'
    
    def __str__(self):
        return self.hospital_name


class SolveyDoctor(models.Model):
    """Solvey doctors_doctors cədvəli"""
    id = models.IntegerField(primary_key=True)
    ad = models.CharField(max_length=255)
    ixtisas = models.CharField(max_length=255, blank=True, null=True)
    kategoriya = models.CharField(max_length=10, blank=True, null=True)
    derece = models.CharField(max_length=10, blank=True, null=True)  # Dərəcə (VIP, I, II, III)
    # vip field-i database-də yoxdur, ona görə silindi - VIP məlumatı derece field-indən alınır
    cinsiyyet = models.CharField(max_length=10, blank=True, null=True)
    number = models.CharField(max_length=50, blank=True, null=True)  # Telefon nömrəsi
    bolge_id = models.IntegerField(null=True, blank=True)
    city_id = models.IntegerField(null=True, blank=True)
    klinika_id = models.IntegerField(null=True, blank=True)
    previous_debt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Əvvəlki borc
    
    class Meta:
        db_table = 'doctors_doctors'
        managed = False
        app_label = 'tracking'
    
    def __str__(self):
        return self.ad

