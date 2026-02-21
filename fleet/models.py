from django.db import models
from django.core.validators import MinValueValidator


class Vehicle(models.Model):
    """Physical fleet asset with lifecycle tracking."""

    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        ON_TRIP = 'on_trip', 'On Trip'
        IN_SHOP = 'in_shop', 'In Shop'
        RETIRED = 'retired', 'Retired'

    class VehicleType(models.TextChoices):
        TRUCK = 'truck', 'Truck'
        VAN = 'van', 'Van'
        BIKE = 'bike', 'Bike'

    name = models.CharField(max_length=100, help_text='Vehicle name/model (e.g. Van-05)')
    license_plate = models.CharField(max_length=20, unique=True, db_index=True)
    vehicle_type = models.CharField(max_length=10, choices=VehicleType.choices, default=VehicleType.VAN)
    capacity = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Max load capacity in kg',
    )
    odometer = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        help_text='Current odometer reading in km',
    )
    acquisition_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
    )
    region = models.CharField(max_length=50, blank=True, default='', help_text='Operating region')
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.AVAILABLE, db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fleet_vehicle'
        ordering = ['name']
        constraints = [
            models.CheckConstraint(
                check=models.Q(capacity__gt=0),
                name='vehicle_capacity_positive',
            ),
            models.CheckConstraint(
                check=models.Q(odometer__gte=0),
                name='vehicle_odometer_non_negative',
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.license_plate})"

    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE

    @property
    def status_color(self):
        return {
            self.Status.AVAILABLE: 'green',
            self.Status.ON_TRIP: 'blue',
            self.Status.IN_SHOP: 'amber',
            self.Status.RETIRED: 'red',
        }.get(self.status, 'gray')


class Maintenance(models.Model):
    """Service/maintenance record for a vehicle."""

    class ServiceType(models.TextChoices):
        OIL_CHANGE = 'oil_change', 'Oil Change'
        TIRE_ROTATION = 'tire_rotation', 'Tire Rotation'
        BRAKE_SERVICE = 'brake_service', 'Brake Service'
        ENGINE_REPAIR = 'engine_repair', 'Engine Repair'
        INSPECTION = 'inspection', 'Inspection'
        OTHER = 'other', 'Other'

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_records')
    service_type = models.CharField(max_length=20, choices=ServiceType.choices)
    description = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    date = models.DateField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fleet_maintenance'
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_service_type_display()} - {self.vehicle.name} ({self.date})"
