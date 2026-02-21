"""
Tests for the Trip operations service layer.
"""
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from fleet.models import Vehicle
from drivers.models import Driver
from operations.models import Trip
from operations.services import dispatch_trip, complete_trip, cancel_trip, TripValidationError

User = get_user_model()


class TripServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testmanager', password='testpass', role='manager')
        self.vehicle = Vehicle.objects.create(
            name='Test-Van-01', license_plate='TEST-001',
            vehicle_type='van', capacity=500, odometer=10000,
            acquisition_cost=500000, region='North India',
        )
        self.driver = Driver.objects.create(
            name='Test Driver', license_number='TDL-001',
            license_expiry=date.today() + timedelta(days=365),
            vehicle_category='van', safety_score=90,
        )

    def _create_draft_trip(self, cargo=200, revenue=10000):
        return Trip.objects.create(
            vehicle=self.vehicle, driver=self.driver,
            origin='Mumbai', destination='Pune',
            cargo_weight=cargo, revenue=revenue,
        )

    def test_dispatch_trip_success(self):
        trip = self._create_draft_trip()
        dispatch_trip(trip, user=self.user)
        trip.refresh_from_db()
        self.vehicle.refresh_from_db()
        self.driver.refresh_from_db()
        self.assertEqual(trip.status, Trip.Status.DISPATCHED)
        self.assertEqual(self.vehicle.status, Vehicle.Status.ON_TRIP)
        self.assertEqual(self.driver.status, Driver.Status.ON_TRIP)
        self.assertEqual(trip.odometer_start, Decimal('10000'))

    def test_dispatch_cargo_exceeds_capacity(self):
        trip = self._create_draft_trip(cargo=600)
        with self.assertRaises(TripValidationError):
            dispatch_trip(trip, user=self.user)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, Vehicle.Status.AVAILABLE)

    def test_dispatch_expired_license(self):
        self.driver.license_expiry = date.today() - timedelta(days=1)
        self.driver.save()
        trip = self._create_draft_trip()
        with self.assertRaises(TripValidationError):
            dispatch_trip(trip, user=self.user)

    def test_dispatch_vehicle_not_available(self):
        self.vehicle.status = Vehicle.Status.IN_SHOP
        self.vehicle.save()
        trip = self._create_draft_trip()
        with self.assertRaises(TripValidationError):
            dispatch_trip(trip, user=self.user)

    def test_dispatch_driver_not_available(self):
        self.driver.status = Driver.Status.SUSPENDED
        self.driver.save()
        trip = self._create_draft_trip()
        with self.assertRaises(TripValidationError):
            dispatch_trip(trip, user=self.user)

    def test_dispatch_category_mismatch(self):
        self.driver.vehicle_category = 'truck'
        self.driver.save()
        trip = self._create_draft_trip()
        with self.assertRaises(TripValidationError):
            dispatch_trip(trip, user=self.user)

    def test_complete_trip_success(self):
        trip = self._create_draft_trip()
        dispatch_trip(trip, user=self.user)
        complete_trip(trip, odometer_end=10500, user=self.user)
        trip.refresh_from_db()
        self.vehicle.refresh_from_db()
        self.driver.refresh_from_db()
        self.assertEqual(trip.status, Trip.Status.COMPLETED)
        self.assertEqual(trip.odometer_end, Decimal('10500'))
        self.assertEqual(self.vehicle.odometer, Decimal('10500'))
        self.assertEqual(self.vehicle.status, Vehicle.Status.AVAILABLE)
        self.assertEqual(self.driver.status, Driver.Status.AVAILABLE)

    def test_complete_odometer_rollback(self):
        trip = self._create_draft_trip()
        dispatch_trip(trip, user=self.user)
        with self.assertRaises(TripValidationError):
            complete_trip(trip, odometer_end=5000, user=self.user)

    def test_cancel_draft_trip(self):
        trip = self._create_draft_trip()
        cancel_trip(trip, user=self.user)
        trip.refresh_from_db()
        self.assertEqual(trip.status, Trip.Status.CANCELLED)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, Vehicle.Status.AVAILABLE)

    def test_cancel_dispatched_trip_restores_statuses(self):
        trip = self._create_draft_trip()
        dispatch_trip(trip, user=self.user)
        cancel_trip(trip, user=self.user)
        trip.refresh_from_db()
        self.vehicle.refresh_from_db()
        self.driver.refresh_from_db()
        self.assertEqual(trip.status, Trip.Status.CANCELLED)
        self.assertEqual(self.vehicle.status, Vehicle.Status.AVAILABLE)
        self.assertEqual(self.driver.status, Driver.Status.AVAILABLE)

    def test_cannot_cancel_completed_trip(self):
        trip = self._create_draft_trip()
        dispatch_trip(trip, user=self.user)
        complete_trip(trip, odometer_end=10500, user=self.user)
        with self.assertRaises(TripValidationError):
            cancel_trip(trip, user=self.user)
