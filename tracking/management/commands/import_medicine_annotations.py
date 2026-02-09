"""
Django management command to import medicine annotations from Word files.
Usage: python manage.py import_medicine_annotations <word_files_directory>
Example: python manage.py import_medicine_annotations /path/to/word/files/
"""
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from tracking.models import Medicine
from tracking.models_solvey import SolveyMedicine

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class Command(BaseCommand):
    help = 'Word fayllarından dərman annotasiyalarını import edir'

    def add_arguments(self, parser):
        parser.add_argument(
            'directory',
            type=str,
            help='Word fayllarının olduğu qovluq yolu'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Yalnız test edir, database-ə yazmır',
        )

    def handle(self, *args, **options):
        if not DOCX_AVAILABLE:
            self.stdout.write(
                self.style.ERROR('❌ python-docx paketi quraşdırılmayıb!')
            )
            self.stdout.write(
                self.style.WARNING('💡 Quraşdırmaq üçün: pip install python-docx')
            )
            return

        directory = options['directory']
        dry_run = options['dry_run']

        if not os.path.isdir(directory):
            self.stdout.write(
                self.style.ERROR(f'❌ Qovluq tapılmadı: {directory}')
            )
            return

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📄 DƏRMAN ANNOTASİYALARI İMPORT'))
        self.stdout.write('='*60 + '\n')

        # Word fayllarını tap
        word_files = [
            f for f in os.listdir(directory)
            if f.endswith(('.docx', '.doc'))
        ]

        if not word_files:
            self.stdout.write(
                self.style.ERROR('❌ Qovluqda Word faylı tapılmadı!')
            )
            return

        self.stdout.write(f'📁 Tapılan Word faylları: {len(word_files)}\n')

        # Solvey database-dən dərmanları çək
        try:
            solvey_medicines = SolveyMedicine.objects.using('external').filter(status=True)
            solvey_dict = {med.id: med for med in solvey_medicines}
            self.stdout.write(f'💊 Solvey database-dən tapılan dərmanlar: {len(solvey_dict)}\n')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Solvey database-dən dərmanlar çəkilə bilmədi: {e}')
            )
            solvey_dict = {}

        imported_count = 0
        updated_count = 0
        error_count = 0

        for word_file in word_files:
            file_path = os.path.join(directory, word_file)
            try:
                # Word faylını oxu
                doc = Document(file_path)
                
                # Bütün mətnləri birləşdir
                full_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                
                if not full_text.strip():
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Boş fayl: {word_file}')
                    )
                    continue

                # Dərman adını fayl adından və ya mətnin ilk sətirindən çıxar
                medicine_name = os.path.splitext(word_file)[0].strip()
                
                # Solvey database-də bu dərmanı tap
                medicine_id = None
                for med_id, med in solvey_dict.items():
                    if (medicine_name.lower() in med.med_name.lower() or 
                        medicine_name.lower() in (med.med_full_name or '').lower() or
                        med.med_name.lower() in medicine_name.lower()):
                        medicine_id = med_id
                        break

                if medicine_id:
                    # Local Medicine modelində dərmanı tap və ya yarat (solvey_id ilə)
                    medicine, created = Medicine.objects.get_or_create(
                        solvey_id=medicine_id,
                        defaults={
                            'name': solvey_dict[medicine_id].med_name,
                            'name_az': solvey_dict[medicine_id].med_full_name or solvey_dict[medicine_id].med_name,
                            'annotation': full_text,
                            'is_active': True,
                        }
                    )
                    
                    if not created:
                        # Artıq varsa, annotasiyanı yenilə
                        medicine.annotation = full_text
                        if not medicine.name:
                            medicine.name = solvey_dict[medicine_id].med_name
                        if not medicine.name_az:
                            medicine.name_az = solvey_dict[medicine_id].med_full_name or solvey_dict[medicine_id].med_name
                        if dry_run:
                            self.stdout.write(
                                self.style.SUCCESS(f'✅ [DRY RUN] Yenilənəcək: {medicine_name} (Solvey ID: {medicine_id})')
                            )
                        else:
                            medicine.save()
                            updated_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'✅ Yeniləndi: {medicine_name} (Solvey ID: {medicine_id}, Local ID: {medicine.id})')
                            )
                    else:
                        if dry_run:
                            self.stdout.write(
                                self.style.SUCCESS(f'✅ [DRY RUN] Əlavə ediləcək: {medicine_name} (Solvey ID: {medicine_id})')
                            )
                        else:
                            imported_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'✅ Əlavə edildi: {medicine_name} (Solvey ID: {medicine_id}, Local ID: {medicine.id})')
                            )
                else:
                    # Solvey database-də tapılmadı, yalnız annotasiya ilə yarat
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  [DRY RUN] Solvey-də tapılmadı, yaradılacaq: {medicine_name}')
                        )
                    else:
                        medicine = Medicine.objects.create(
                            name=medicine_name,
                            name_az=medicine_name,
                            annotation=full_text,
                            is_active=True,
                        )
                        imported_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ Yeni dərman əlavə edildi: {medicine_name} (ID: {medicine.id})')
                        )

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Xəta ({word_file}): {str(e)}')
                )

        # Nəticə
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - Database-ə yazılmadı'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Əlavə edildi: {imported_count}'))
            self.stdout.write(self.style.SUCCESS(f'🔄 Yeniləndi: {updated_count}'))
        self.stdout.write(self.style.ERROR(f'❌ Xəta: {error_count}'))
        self.stdout.write('='*60 + '\n')
