# Server-də Dərman Annotasiyalarını Import Etmək

## Addım 1: Faylları Serverə Yükləyin

Dərman annotasiya fayllarını serverə yükləyin. Məsələn:
```bash
# SSH ilə serverə qoşulun
ssh user@your-server

# Faylları yükləyin (məsələn /var/www/flux-backend/drug/ qovluğuna)
# Siz 22 dərmanın annotasiya fayllarını bu qovluğa yükləyin
```

## Addım 2: Migration-ləri Tətbiq Edin

```bash
cd /var/www/flux-backend
source venv/bin/activate  # Virtual environment aktivləşdirin
python manage.py migrate tracking
```

## Addım 3: Import Command-i Çalıştırın

### Test modu (database-ə yazmır):
```bash
python manage.py import_medicine_annotations /var/www/flux-backend/drug --dry-run
```

### Real import:
```bash
python manage.py import_medicine_annotations /var/www/flux-backend/drug
```

## Addım 4: Nəticəni Yoxlayın

Import tamamlandıqdan sonra, mobile app-də dərmanlar səhifəsini açın və annotasiyaların göründüyünü yoxlayın.

## Qeydlər:

- Əgər external database konfiqurasiya olunmayıbsa, annotasiyalar yalnız local database-ə yazılacaq
- Solvey database-də dərman varsa, annotasiya avtomatik olaraq uyğunlaşdırılacaq
- Əgər Solvey database-də dərman yoxdursa, yeni dərman yaradılacaq

## Fayl Formatı:

- Text faylları: `.txt` və ya extension olmadan
- Word faylları: `.docx` və ya `.doc`
- Fayl adı dərman adı olmalıdır (məsələn: `OBeblock`, `Aspirin.txt`)
