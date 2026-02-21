from django.db import models
from django.utils import timezone


class Driver(models.Model):
    """Driver resource with compliance tracking."""

    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        ON_TRIP = 'on_trip', 'On Trip'
        OFF_DUTY = 'off_duty', 'Off Duty'
        SUSPENDED = 'suspended', 'Suspended'

    class VehicleCategory(models.TextChoices):
        TRUCK = 'truck', 'Truck'
        VAN = 'van', 'Van'
        BIKE = 'bike', 'Bike'
        ALL = 'all', 'All Categories'

    name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True, db_index=True)
    license_expiry = models.DateField(help_text='License expiration date')
    vehicle_category = models.CharField(
        max_length=10, choices=VehicleCategory.choices, default=VehicleCategory.VAN,
        help_text='Category of vehicles this driver can operate',
    )
    phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.AVAILABLE, db_index=True,
    )
    safety_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=100.00,
        help_text='Safety score (0-100)',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'drivers_driver'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.license_number})"

    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE

    @property
    def is_license_valid(self):
        return self.license_expiry >= timezone.now().date()

    @property
    def is_license_expiring_soon(self):
        days_left = (self.license_expiry - timezone.now().date()).days
        return 0 < days_left <= 30

    @property
    def status_color(self):
        return {
            self.Status.AVAILABLE: 'green',
            self.Status.ON_TRIP: 'blue',
            self.Status.OFF_DUTY: 'gray',
            self.Status.SUSPENDED: 'red',
        }.get(self.status, 'gray')

    @property
    def trip_completion_rate(self):
        total = self.trips.exclude(status='draft').count()
        if total == 0:
            return 0
        completed = self.trips.filter(status='completed').count()
        return round((completed / total) * 100, 1)
