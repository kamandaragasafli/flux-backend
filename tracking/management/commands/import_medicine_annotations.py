"""
Django management command to import medicine annotations from text files.
Usage: python manage.py import_medicine_annotations <files_directory>
Example: python manage.py import_medicine_annotations /path/to/drug/files/
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
    help = 'Text və Word fayllarından dərman annotasiyalarını import edir'

    def add_arguments(self, parser):
        parser.add_argument(
            'directory',
            type=str,
            help='Annotasiya fayllarının olduğu qovluq yolu'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Yalnız test edir, database-ə yazmır',
        )

    def read_text_file(self, file_path):
        """Text faylını oxuyur və mətn qaytarır"""
        try:
            # Müxtəlif encoding-ləri yoxla
            encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'windows-1251']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            # Əgər heç biri işləməsə, binary mode ilə oxu
            with open(file_path, 'rb') as f:
                content = f.read()
                return content.decode('utf-8', errors='ignore')
        except Exception as e:
            raise Exception(f"Fayl oxuna bilmədi: {e}")

    def parse_annotation(self, content):
        """Annotasiya mətnini parse edir və strukturlaşdırır"""
        lines = content.split('\n')
        annotation_text = content.strip()
        
        # Dərman adını ilk sətirdən çıxar (boşluqları təmizlə)
        medicine_name = lines[0].strip() if lines else ''
        
        return {
            'name': medicine_name,
            'annotation': annotation_text,
        }

    def handle(self, *args, **options):
        directory = options['directory']
        dry_run = options['dry_run']

        if not os.path.isdir(directory):
            self.stdout.write(
                self.style.ERROR(f'Qovluq tapilmadi: {directory}')
            )
            return

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('DERMAN ANNOTASIYALARI IMPORT'))
        self.stdout.write('='*60 + '\n')

        # Bütün faylları tap (text və Word)
        all_files = []
        for f in os.listdir(directory):
            file_path = os.path.join(directory, f)
            if os.path.isfile(file_path):
                # Text faylları (extension olmadan və ya .txt)
                if not f.endswith(('.docx', '.doc')) or f.endswith(('.txt', '')):
                    all_files.append(f)
                # Word faylları
                elif f.endswith(('.docx', '.doc')):
                    all_files.append(f)

        if not all_files:
            self.stdout.write(
                self.style.ERROR('Qovluqda fayl tapilmadi!')
            )
            return

        self.stdout.write(f'Tapilan fayllar: {len(all_files)}\n')

        # Solvey database-dən dərmanları çək
        solvey_dict = {}
        try:
            from django.db import connections
            import os as os_module
            
            # External database connection-u yoxla
            if 'external' not in connections.databases:
                self.stdout.write(
                    self.style.WARNING('Xeberdarliq: External database konfiqurasiya olunmayib. Solvey database-den dermanlar cekilmeyecek.')
                )
            else:
                medicines_table = os_module.getenv('SOLVEY_MEDICINES_TABLE', 'medicine_medical')
                
                with connections['external'].cursor() as cursor:
                    cursor.execute(f"""
                        SELECT id, med_name, med_full_name
                        FROM "{medicines_table}"
                        WHERE status = true
                    """)
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        med_data = dict(zip(columns, row))
                        solvey_dict[med_data['id']] = med_data
                
                self.stdout.write(f'Solvey database-den tapilan dermanlar: {len(solvey_dict)}\n')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Xeberdarliq: Solvey database-den dermanlar cekile bilmedi: {e}')
            )

        imported_count = 0
        updated_count = 0
        error_count = 0

        for file_name in all_files:
            file_path = os.path.join(directory, file_name)
            try:
                # Fayl tipini müəyyən et
                is_word_file = file_name.endswith(('.docx', '.doc'))
                
                if is_word_file:
                    if not DOCX_AVAILABLE:
                        self.stdout.write(
                            self.style.WARNING(f'Xeberdarliq: Word fayli oxuna bilmedi (python-docx yoxdur): {file_name}')
                        )
                        error_count += 1
                        continue
                    
                    # Word faylını oxu
                    doc = Document(file_path)
                    full_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                else:
                    # Text faylını oxu
                    full_text = self.read_text_file(file_path)
                
                if not full_text.strip():
                    self.stdout.write(
                        self.style.WARNING(f'Xeberdarliq: Bos fayl: {file_name}')
                    )
                    continue

                # Annotasiyanı parse et
                parsed = self.parse_annotation(full_text)
                medicine_name_from_file = parsed['name']
                annotation_text = parsed['annotation']
                
                # Dərman adını fayl adından və ya mətnin ilk sətirindən çıxar
                medicine_name = os.path.splitext(file_name)[0].strip()
                if not medicine_name or medicine_name == file_name:
                    medicine_name = medicine_name_from_file.strip()
                
                # Dərman adını normalize et (böyük hərflərlə)
                medicine_name_normalized = medicine_name.upper().strip()
                
                # Solvey database-də bu dərmanı tap
                medicine_id = None
                matched_med = None
                
                for med_id, med in solvey_dict.items():
                    med_name = (med.get('med_name') or '').upper().strip()
                    med_full_name = (med.get('med_full_name') or '').upper().strip()
                    
                    # Dərman adını müqayisə et
                    if (medicine_name_normalized in med_name or 
                        medicine_name_normalized in med_full_name or
                        med_name in medicine_name_normalized or
                        med_full_name in medicine_name_normalized):
                        medicine_id = med_id
                        matched_med = med
                        break
                
                # Əgər tapılmadısa, fayl adı ilə də yoxla
                if not medicine_id:
                    for med_id, med in solvey_dict.items():
                        med_name = (med.get('med_name') or '').upper().strip()
                        med_full_name = (med.get('med_full_name') or '').upper().strip()
                        file_base_name = os.path.splitext(file_name)[0].upper().strip()
                        
                        if (file_base_name in med_name or 
                            file_base_name in med_full_name or
                            med_name in file_base_name):
                            medicine_id = med_id
                            matched_med = med
                            break

                if medicine_id and matched_med:
                    # Local Medicine modelində dərmanı tap və ya yarat (solvey_id ilə)
                    medicine, created = Medicine.objects.get_or_create(
                        solvey_id=medicine_id,
                        defaults={
                            'name': matched_med.get('med_name') or medicine_name,
                            'name_az': matched_med.get('med_full_name') or matched_med.get('med_name') or medicine_name,
                            'annotation': annotation_text,
                            'is_active': True,
                        }
                    )
                    
                    if not created:
                        # Artıq varsa, annotasiyanı yenilə
                        medicine.annotation = annotation_text
                        if not medicine.name:
                            medicine.name = matched_med.get('med_name') or medicine_name
                        if not medicine.name_az:
                            medicine.name_az = matched_med.get('med_full_name') or matched_med.get('med_name') or medicine_name
                        if dry_run:
                            self.stdout.write(
                                self.style.SUCCESS(f'[DRY RUN] Yenilenecek: {medicine_name} (Solvey ID: {medicine_id})')
                            )
                        else:
                            medicine.save()
                            updated_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'Yenilendi: {medicine_name} (Solvey ID: {medicine_id}, Local ID: {medicine.id})')
                            )
                    else:
                        if dry_run:
                            self.stdout.write(
                                self.style.SUCCESS(f'[DRY RUN] Elave edilecek: {medicine_name} (Solvey ID: {medicine_id})')
                            )
                        else:
                            imported_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'Elave edildi: {medicine_name} (Solvey ID: {medicine_id}, Local ID: {medicine.id})')
                            )
                else:
                    # Solvey database-də tapılmadı, yalnız annotasiya ilə yarat
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(f'[DRY RUN] Solvey-de tapilmadi, yaradilacaq: {medicine_name}')
                        )
                    else:
                        medicine = Medicine.objects.create(
                            name=medicine_name,
                            name_az=medicine_name,
                            annotation=annotation_text,
                            is_active=True,
                        )
                        imported_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Yeni derman elave edildi: {medicine_name} (ID: {medicine.id})')
                        )

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Xeta ({file_name}): {str(e)}')
                )

        # Nəticə
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - Database-e yazilmadi'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Elave edildi: {imported_count}'))
            self.stdout.write(self.style.SUCCESS(f'Yenilendi: {updated_count}'))
        self.stdout.write(self.style.ERROR(f'Xeta: {error_count}'))
        self.stdout.write('='*60 + '\n')
