"""Audit logging utility for state changes."""
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog


def log_state_change(instance, user, field_name, old_value, new_value, message=''):
    """Create an audit log entry for a state change."""
    ct = ContentType.objects.get_for_model(instance)
    AuditLog.objects.create(
        content_type=ct,
        object_id=instance.pk,
        user=user,
        action='status_change',
        field_name=field_name,
        old_value=str(old_value),
        new_value=str(new_value),
        message=message,
    )


def log_creation(instance, user, message=''):
    """Create an audit log entry for object creation."""
    ct = ContentType.objects.get_for_model(instance)
    AuditLog.objects.create(
        content_type=ct,
        object_id=instance.pk,
        user=user,
        action='created',
        message=message or f'{ct.model.title()} created',
    )
