from django.contrib import admin
from .models import Driver


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'license_number', 'license_expiry', 'vehicle_category', 'status', 'safety_score')
    list_filter = ('status', 'vehicle_category')
    search_fields = ('name', 'license_number')
