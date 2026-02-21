from django.contrib import admin
from .models import Vehicle, Maintenance


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'license_plate', 'vehicle_type', 'capacity', 'odometer', 'status', 'region')
    list_filter = ('status', 'vehicle_type', 'region')
    search_fields = ('name', 'license_plate')


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'service_type', 'cost', 'date', 'is_resolved')
    list_filter = ('service_type', 'is_resolved')
