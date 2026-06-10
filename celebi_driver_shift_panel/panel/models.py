from django.conf import settings
from django.db import models
from django.utils import timezone


class DriverGroup(models.Model):
    name = models.CharField(max_length=80, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['name']
        verbose_name = 'Sürücü Grubu'
        verbose_name_plural = 'Sürücü Grupları'

    def __str__(self):
        return self.name


class Driver(models.Model):
    full_name = models.CharField(max_length=150, unique=True, db_index=True)
    group = models.ForeignKey(DriverGroup, on_delete=models.PROTECT, related_name='drivers')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Sürücü'
        verbose_name_plural = 'Sürücüler'

    def __str__(self):
        return self.full_name


class Vehicle(models.Model):
    plate = models.CharField(max_length=40, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['plate']
        verbose_name = 'Plaka'
        verbose_name_plural = 'Plakalar'

    def __str__(self):
        return self.plate


class ShiftRecord(models.Model):
    operation_date = models.DateField(db_index=True)
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name='shift_records')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='shift_records', null=True, blank=True)
    shift_start = models.TimeField()
    shift_end = models.TimeField()
    vehicle_pickup_time = models.TimeField(null=True, blank=True)
    vehicle_dropoff_time = models.TimeField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_shift_records')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_shift_records')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-operation_date', 'shift_start', 'driver__full_name']
        indexes = [
            models.Index(fields=['operation_date', 'driver']),
            models.Index(fields=['operation_date', 'vehicle']),
        ]
        verbose_name = 'Vardiya Kaydı'
        verbose_name_plural = 'Vardiya Kayıtları'

    def __str__(self):
        return f'{self.operation_date} - {self.driver} - {self.vehicle or "Plakasız"}'
