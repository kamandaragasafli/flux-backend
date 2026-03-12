from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0014_add_route_battery_level'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VisitedPharmacy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pharmacy_name', models.CharField(max_length=255, verbose_name='Aptek adı')),
                ('visit_type', models.CharField(choices=[('sale', 'Satış'), ('order', 'Sifariş')], max_length=20, verbose_name='Növü')),
                ('medicine_name', models.CharField(blank=True, max_length=255, verbose_name='Dərman adı (əl ilə)')),
                ('notes', models.TextField(blank=True, verbose_name='Qeyd')),
                ('visit_date', models.DateTimeField(auto_now_add=True)),
                ('medicine', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='pharmacy_visits',
                    to='tracking.medicine',
                    verbose_name='Dərman (DB-dən)',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='visited_pharmacies',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Görülən Aptek',
                'verbose_name_plural': 'Görülən Apteklər',
                'ordering': ['-visit_date'],
            },
        ),
    ]
