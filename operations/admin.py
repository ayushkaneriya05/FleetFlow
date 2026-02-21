from django.contrib import admin
from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehicle', 'driver', 'origin', 'destination', 'cargo_weight', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('origin', 'destination')
