from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with role-based access control."""

    class Role(models.TextChoices):
        MANAGER = 'manager', 'Fleet Manager'
        DISPATCHER = 'dispatcher', 'Dispatcher'
        SAFETY_OFFICER = 'safety_officer', 'Safety Officer'
        ANALYST = 'analyst', 'Financial Analyst'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DISPATCHER,
    )
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'accounts_user'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def is_dispatcher(self):
        return self.role == self.Role.DISPATCHER

    @property
    def is_safety_officer(self):
        return self.role == self.Role.SAFETY_OFFICER

    @property
    def is_analyst(self):
        return self.role == self.Role.ANALYST
