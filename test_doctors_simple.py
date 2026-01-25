"""
Sadə test script - hər bölgədən 10 həkim göstərir
İstifadə: python test_doctors_simple.py
"""
import os
import sys
import django

# Django setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tracker.settings')
django.setup()

from django.db import connections
from tracking.models_solvey import SolveyRegion, SolveyDoctor, SolveyHospital


def test_doctors():
    print('\n' + '='*60)
    print('🏥 HƏKİMLƏR TESTİ')
    print('='*60 + '\n')

    # External database connection-u yoxla
    use_external = 'external' in connections.databases
    db_alias = 'external' if use_external else 'default'
    
    if not use_external:
        print('⚠️  External database konfiqurasiya olunmayıb, default database istifadə olunur.')
        print('💡 Database router avtomatik olaraq external database-ə yönləndirəcək.\n')
        db_alias = None  # Database router istifadə etsin

    try:
        # Bütün bölgələri çək
        if db_alias:
            regions = SolveyRegion.objects.using(db_alias).all().order_by('id')
        else:
            regions = SolveyRegion.objects.all().order_by('id')
        
        if not regions.exists():
            print('❌ Heç bir bölgə tapılmadı!')
            return

        total_doctors = 0
        
        for region in regions:
            # Bu bölgədəki həkimləri çək
            if db_alias:
                doctors = SolveyDoctor.objects.using(db_alias).filter(bolge_id=region.id).order_by('ad')[:10]
            else:
                doctors = SolveyDoctor.objects.filter(bolge_id=region.id).order_by('ad')[:10]
            
            if not doctors.exists():
                continue
            
            # Bölgə məlumatlarını göstər
            print('\n' + '='*60)
            print(f'🏥 BÖLGƏ: {region.region_name} (ID: {region.id})')
            
            # Ümumi həkim sayını tap
            if db_alias:
                total_in_region = SolveyDoctor.objects.using(db_alias).filter(bolge_id=region.id).count()
            else:
                total_in_region = SolveyDoctor.objects.filter(bolge_id=region.id).count()
            print(f'📊 Ümumi həkim sayı: {total_in_region}')
            print(f'👨‍⚕️ İlk 10 həkim:')
            print('='*60)
            
            # Hər həkim üçün məlumat göstər
            for index, doctor in enumerate(doctors, 1):
                # Xəstəxana adını tap
                hospital_name = 'Yoxdur'
                if doctor.klinika_id:
                    try:
                        if db_alias:
                            hospital = SolveyHospital.objects.using(db_alias).filter(id=doctor.klinika_id).first()
                        else:
                            hospital = SolveyHospital.objects.filter(id=doctor.klinika_id).first()
                        if hospital:
                            hospital_name = hospital.hospital_name or 'Yoxdur'
                    except Exception as e:
                        print(f'   ⚠️  Xəstəxana tapılmadı: {e}')
                        pass
                
                # Dərəcə və VIP parsing
                derece_value = doctor.derece or ''
                vip_value = ''
                degree_value = ''
                
                if derece_value:
                    derece_str = str(derece_value).strip().upper()
                    if derece_str == 'VIP':
                        vip_value = 'VIP'
                        degree_value = ''
                    elif derece_str.startswith('VIP'):
                        vip_value = 'VIP'
                        degree_value = derece_str.replace('VIP', '').strip()
                    else:
                        degree_value = derece_str
                        vip_value = ''
                
                # Badge-ləri formatla
                badges = []
                if vip_value:
                    badges.append(f'[VIP]')
                if degree_value:
                    badges.append(f'[{degree_value}]')
                badges_str = ' '.join(badges) if badges else '[Dərəcə yoxdur]'
                
                # Həkim məlumatlarını göstər
                print(f'\n{index}. {doctor.ad or "Naməlum Həkim"}')
                print(f'   📋 İxtisas: {doctor.ixtisas or "Naməlum"}')
                print(f'   🏥 Xəstəxana: {hospital_name}')
                print(f'   📞 Telefon: {doctor.number or "Yoxdur"}')
                print(f'   🏷️  Dərəcə: {badges_str}')
                print(f'   📊 Kateqoriya: {doctor.kategoriya or "A"}')
                print(f'   👤 Cinsiyyət: {doctor.cinsiyyet or "Naməlum"}')
            
            total_doctors += doctors.count()
        
        # Ümumi statistika
        print('\n' + '='*60)
        print(f'✅ Ümumi göstərilən həkim sayı: {total_doctors}')
        print('='*60 + '\n')
        
    except Exception as e:
        import traceback
        print(f'\n❌ Xəta: {e}')
        print(f'Traceback:\n{traceback.format_exc()}')


if __name__ == '__main__':
    test_doctors()

