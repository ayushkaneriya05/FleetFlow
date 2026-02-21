from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'content_type', 'object_id', 'user', 'field_name', 'old_value', 'new_value')
    list_filter = ('action', 'content_type', 'timestamp')
    readonly_fields = ('content_type', 'object_id', 'user', 'action', 'field_name', 'old_value', 'new_value', 'message', 'timestamp')
