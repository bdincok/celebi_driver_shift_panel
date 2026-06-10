from django.contrib import admin
from .models import DriverGroup, Driver, Vehicle, ShiftRecord


@admin.register(DriverGroup)
class DriverGroupAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'group', 'is_active', 'updated_at']
    list_filter = ['group', 'is_active']
    search_fields = ['full_name']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['plate', 'is_active', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['plate']


@admin.register(ShiftRecord)
class ShiftRecordAdmin(admin.ModelAdmin):
    list_display = ['operation_date', 'driver', 'vehicle', 'shift_start', 'shift_end', 'vehicle_pickup_time', 'vehicle_dropoff_time']
    list_filter = ['operation_date', 'driver__group', 'vehicle']
    search_fields = ['driver__full_name', 'vehicle__plate', 'note']
    date_hierarchy = 'operation_date'
