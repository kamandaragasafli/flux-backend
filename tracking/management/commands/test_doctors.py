"""
Django management command to test doctors from each region.
Usage: python manage.py test_doctors
"""
from django.core.management.base import BaseCommand
from django.db import connections
from tracking.models_solvey import SolveyRegion, SolveyDoctor, SolveyHospital


class Command(BaseCommand):
    help = 'Hər bölgədən 10 həkim göstərir terminalda'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🏥 HƏKİMLƏR TESTİ'))
        self.stdout.write('='*60 + '\n')

        # External database connection-u yoxla
        if 'external' not in connections.databases:
            self.stdout.write(self.style.ERROR('❌ External database konfiqurasiya olunmayıb!'))
            self.stdout.write(self.style.WARNING('💡 .env faylında USE_EXTERNAL_DB=true və external database parametrlərini yoxlayın.'))
            return

        # Bütün bölgələri çək (external database-dən)
        regions = SolveyRegion.objects.using('external').all().order_by('id')
        
        if not regions.exists():
            self.stdout.write(self.style.ERROR('❌ Heç bir bölgə tapılmadı!'))
            return

        total_doctors = 0
        
        for region in regions:
            # Bu bölgədəki həkimləri çək (external database-dən)
            doctors = SolveyDoctor.objects.using('external').filter(bolge_id=region.id).order_by('ad')[:10]
            
            if not doctors.exists():
                continue
            
            # Bölgə məlumatlarını göstər
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS(f'🏥 BÖLGƏ: {region.region_name} (ID: {region.id})'))
            
            # Ümumi həkim sayını tap
            total_in_region = SolveyDoctor.objects.using('external').filter(bolge_id=region.id).count()
            self.stdout.write(f'📊 Ümumi həkim sayı: {total_in_region}')
            self.stdout.write(f'👨‍⚕️ İlk 10 həkim:')
            self.stdout.write('='*60)
            
            # Hər həkim üçün məlumat göstər
            for index, doctor in enumerate(doctors, 1):
                # Xəstəxana adını tap
                hospital_name = 'Yoxdur'
                if doctor.klinika_id:
                    try:
                        hospital = SolveyHospital.objects.using('external').filter(id=doctor.klinika_id).first()
                        if hospital:
                            hospital_name = hospital.hospital_name or 'Yoxdur'
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'   ⚠️  Xəstəxana tapılmadı: {e}'))
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
                self.stdout.write(f'\n{index}. {doctor.ad or "Naməlum Həkim"}')
                self.stdout.write(f'   📋 İxtisas: {doctor.ixtisas or "Naməlum"}')
                self.stdout.write(f'   🏥 Xəstəxana: {hospital_name}')
                self.stdout.write(f'   📞 Telefon: {doctor.number or "Yoxdur"}')
                self.stdout.write(f'   🏷️  Dərəcə: {badges_str}')
                self.stdout.write(f'   📊 Kateqoriya: {doctor.kategoriya or "A"}')
                self.stdout.write(f'   👤 Cinsiyyət: {doctor.cinsiyyet or "Naməlum"}')
            
            total_doctors += doctors.count()
        
        # Ümumi statistika
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ Ümumi göstərilən həkim sayı: {total_doctors}'))
        self.stdout.write('='*60 + '\n')

