from django.db import models
from django.core.validators import MinValueValidator
from fleet.models import Vehicle
from drivers.models import Driver


class Trip(models.Model):
    """Business transaction: moving cargo from origin to destination."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        DISPATCHED = 'dispatched', 'Dispatched'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='trips')
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name='trips')
    origin = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    cargo_weight = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Cargo weight in kg',
    )
    revenue = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
    )
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.DRAFT, db_index=True,
    )
    odometer_start = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    odometer_end = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'operations_trip'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(cargo_weight__gt=0),
                name='trip_cargo_weight_positive',
            ),
        ]

    def __str__(self):
        return f"Trip #{self.pk} — {self.origin} → {self.destination} ({self.get_status_display()})"

    @property
    def distance(self):
        if self.odometer_start is not None and self.odometer_end is not None:
            return self.odometer_end - self.odometer_start
        return None

    @property
    def status_color(self):
        return {
            self.Status.DRAFT: 'gray',
            self.Status.DISPATCHED: 'blue',
            self.Status.COMPLETED: 'green',
            self.Status.CANCELLED: 'red',
        }.get(self.status, 'gray')
