from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_old_medicine_to_items(apps, schema_editor):
    VisitedPharmacy = apps.get_model('tracking', 'VisitedPharmacy')
    VisitedPharmacyItem = apps.get_model('tracking', 'VisitedPharmacyItem')
    for vp in VisitedPharmacy.objects.filter(medicine__isnull=False):
        VisitedPharmacyItem.objects.get_or_create(
            visited_pharmacy=vp,
            medicine=vp.medicine,
            defaults={'quantity': 1}
        )


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0015_visitedpharmacy'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VisitedPharmacyItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Say')),
                ('medicine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pharmacy_visit_items', to='tracking.medicine')),
                ('visited_pharmacy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='tracking.visitedpharmacy')),
            ],
            options={
                'verbose_name': 'Aptek dərmanı',
                'verbose_name_plural': 'Aptek dərmanları',
                'unique_together': {('visited_pharmacy', 'medicine')},
            },
        ),
        migrations.RunPython(migrate_old_medicine_to_items, migrations.RunPython.noop),
        migrations.RemoveField(model_name='visitedpharmacy', name='medicine'),
        migrations.RemoveField(model_name='visitedpharmacy', name='medicine_name'),
    ]
