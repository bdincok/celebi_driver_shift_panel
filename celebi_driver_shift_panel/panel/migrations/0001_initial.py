# Generated manually for ISTCLB Driver Panel
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DriverGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Sürücü Grubu',
                'verbose_name_plural': 'Sürücü Grupları',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plate', models.CharField(db_index=True, max_length=40, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Plaka',
                'verbose_name_plural': 'Plakalar',
                'ordering': ['plate'],
            },
        ),
        migrations.CreateModel(
            name='Driver',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(db_index=True, max_length=150, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='drivers', to='panel.drivergroup')),
            ],
            options={
                'verbose_name': 'Sürücü',
                'verbose_name_plural': 'Sürücüler',
                'ordering': ['full_name'],
            },
        ),
        migrations.CreateModel(
            name='ShiftRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operation_date', models.DateField(db_index=True)),
                ('shift_start', models.TimeField()),
                ('shift_end', models.TimeField()),
                ('vehicle_pickup_time', models.TimeField(blank=True, null=True)),
                ('vehicle_dropoff_time', models.TimeField(blank=True, null=True)),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_shift_records', to=settings.AUTH_USER_MODEL)),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='shift_records', to='panel.driver')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_shift_records', to=settings.AUTH_USER_MODEL)),
                ('vehicle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='shift_records', to='panel.vehicle')),
            ],
            options={
                'verbose_name': 'Vardiya Kaydı',
                'verbose_name_plural': 'Vardiya Kayıtları',
                'ordering': ['-operation_date', 'shift_start', 'driver__full_name'],
            },
        ),
        migrations.AddIndex(
            model_name='shiftrecord',
            index=models.Index(fields=['operation_date', 'driver'], name='panel_shift_operati_f1bd56_idx'),
        ),
        migrations.AddIndex(
            model_name='shiftrecord',
            index=models.Index(fields=['operation_date', 'vehicle'], name='panel_shift_operati_c2ec4c_idx'),
        ),
    ]
