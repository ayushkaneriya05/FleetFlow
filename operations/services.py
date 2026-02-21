"""
Service layer for Trip operations.
All state transitions are atomic and enforce business rules.
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from fleet.models import Vehicle
from drivers.models import Driver
from .models import Trip
from core.audit import log_state_change, log_creation


class TripValidationError(Exception):
    """Raised when a trip operation fails validation."""
    pass


def validate_dispatch(vehicle, driver, cargo_weight):
    errors = []
    if vehicle.status != Vehicle.Status.AVAILABLE:
        errors.append(f'Vehicle "{vehicle.name}" is not available (current status: {vehicle.get_status_display()}).')
    if vehicle.status == Vehicle.Status.RETIRED:
        errors.append(f'Vehicle "{vehicle.name}" has been retired and cannot be assigned.')
    if driver.status != Driver.Status.AVAILABLE:
        errors.append(f'Driver "{driver.name}" is not available (current status: {driver.get_status_display()}).')
    if not driver.is_license_valid:
        errors.append(f'Driver "{driver.name}" has an expired license (expired: {driver.license_expiry}).')
    if driver.status == Driver.Status.SUSPENDED:
        errors.append(f'Driver "{driver.name}" is suspended and cannot be assigned.')
    if Decimal(str(cargo_weight)) > vehicle.capacity:
        errors.append(f'Cargo weight ({cargo_weight} kg) exceeds vehicle capacity ({vehicle.capacity} kg).')
    if driver.vehicle_category != 'all' and driver.vehicle_category != vehicle.vehicle_type:
        errors.append(
            f'Driver "{driver.name}" is licensed for {driver.get_vehicle_category_display()} '
            f'but vehicle "{vehicle.name}" is a {vehicle.get_vehicle_type_display()}.'
        )
    if errors:
        raise TripValidationError(errors)


@transaction.atomic
def dispatch_trip(trip, user=None):
    if trip.status != Trip.Status.DRAFT:
        raise TripValidationError([f'Trip #{trip.pk} is not in Draft status.'])

    vehicle = Vehicle.objects.select_for_update().get(pk=trip.vehicle_id)
    driver = Driver.objects.select_for_update().get(pk=trip.driver_id)

    validate_dispatch(vehicle, driver, trip.cargo_weight)

    trip.odometer_start = vehicle.odometer
    old_trip_status = trip.status
    trip.status = Trip.Status.DISPATCHED
    trip.save()

    old_vehicle_status = vehicle.status
    vehicle.status = Vehicle.Status.ON_TRIP
    vehicle.save()

    old_driver_status = driver.status
    driver.status = Driver.Status.ON_TRIP
    driver.save()

    log_state_change(trip, user, 'status', old_trip_status, trip.status, f'Trip dispatched with {trip.cargo_weight}kg cargo')
    log_state_change(vehicle, user, 'status', old_vehicle_status, vehicle.status, f'Assigned to Trip #{trip.pk}')
    log_state_change(driver, user, 'status', old_driver_status, driver.status, f'Assigned to Trip #{trip.pk}')

    return trip


@transaction.atomic
def complete_trip(trip, odometer_end, user=None):
    if trip.status != Trip.Status.DISPATCHED:
        raise TripValidationError([f'Trip #{trip.pk} is not in Dispatched status.'])

    vehicle = Vehicle.objects.select_for_update().get(pk=trip.vehicle_id)
    driver = Driver.objects.select_for_update().get(pk=trip.driver_id)

    odometer_end = Decimal(str(odometer_end))
    if odometer_end < vehicle.odometer:
        raise TripValidationError([
            f'End odometer ({odometer_end}) cannot be less than current odometer ({vehicle.odometer}).'
        ])

    old_trip_status = trip.status
    trip.odometer_end = odometer_end
    trip.status = Trip.Status.COMPLETED
    trip.save()

    old_vehicle_status = vehicle.status
    vehicle.odometer = odometer_end
    vehicle.status = Vehicle.Status.AVAILABLE
    vehicle.save()

    old_driver_status = driver.status
    driver.status = Driver.Status.AVAILABLE
    driver.save()

    log_state_change(trip, user, 'status', old_trip_status, trip.status, f'Trip completed. Distance: {trip.distance} km')
    log_state_change(vehicle, user, 'status', old_vehicle_status, vehicle.status, f'Returned from Trip #{trip.pk}')
    log_state_change(driver, user, 'status', old_driver_status, driver.status, f'Returned from Trip #{trip.pk}')

    return trip


@transaction.atomic
def cancel_trip(trip, user=None):
    if trip.status not in (Trip.Status.DRAFT, Trip.Status.DISPATCHED):
        raise TripValidationError([f'Trip #{trip.pk} cannot be cancelled (status: {trip.get_status_display()}).'])

    old_trip_status = trip.status
    was_dispatched = trip.status == Trip.Status.DISPATCHED

    trip.status = Trip.Status.CANCELLED
    trip.save()

    log_state_change(trip, user, 'status', old_trip_status, trip.status, 'Trip cancelled')

    if was_dispatched:
        vehicle = Vehicle.objects.select_for_update().get(pk=trip.vehicle_id)
        driver = Driver.objects.select_for_update().get(pk=trip.driver_id)

        old_v = vehicle.status
        vehicle.status = Vehicle.Status.AVAILABLE
        vehicle.save()
        log_state_change(vehicle, user, 'status', old_v, vehicle.status, f'Released from cancelled Trip #{trip.pk}')

        old_d = driver.status
        driver.status = Driver.Status.AVAILABLE
        driver.save()
        log_state_change(driver, user, 'status', old_d, driver.status, f'Released from cancelled Trip #{trip.pk}')

    return trip
