"""
Görülən həkimləri günlük sıfırla.
Hər gün çalışdırılmalıdır (cron: 0 0 * * * = hər gecə 00:00).
"""
from django.core.management.base import BaseCommand
from tracking.models import VisitedDoctor


class Command(BaseCommand):
    help = "VisitedDoctor qeydlərini silər (günlük sıfırlama üçün)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Silmə — yalnız neçə qeyd silinəcəyini göstər",
        )

    def handle(self, *args, **options):
        count = VisitedDoctor.objects.count()
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING(f"[DRY-RUN] {count} qeyd silinəcək"))
            return
        deleted, _ = VisitedDoctor.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Görülən həkimlər sıfırlandı: {deleted} qeyd silindi"))
