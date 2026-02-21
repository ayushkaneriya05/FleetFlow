"""
Management command to seed the database with realistic demo data.
Usage: python manage.py seed_demo_data
"""
import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from fleet.models import Vehicle, Maintenance
from drivers.models import Driver
from operations.models import Trip
from finance.models import Expense

User = get_user_model()

REGIONS = ['North India', 'South India', 'West India', 'East India']
CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow']


class Command(BaseCommand):
    help = 'Seed database with realistic demo data for FleetFlow'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Seeding FleetFlow database...\n')

        # ── Users ──
        users = {}
        user_data = [
            ('admin', 'admin@fleetflow.io', 'manager', 'Admin', 'User'),
            ('dispatcher1', 'dispatch@fleetflow.io', 'dispatcher', 'Ravi', 'Kumar'),
            ('safety1', 'safety@fleetflow.io', 'safety_officer', 'Priya', 'Sharma'),
            ('analyst1', 'analyst@fleetflow.io', 'analyst', 'Arjun', 'Patel'),
        ]
        for username, email, role, first, last in user_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'role': role,
                    'first_name': first,
                    'last_name': last,
                    'is_staff': role == 'manager',
                    'is_superuser': username == 'admin',
                }
            )
            if created:
                user.set_password('fleetflow123')
                user.save()
            users[role] = user

        self.stdout.write(f'  ✅ {len(user_data)} users created (password: fleetflow123)')

        # ── Vehicles ──
        vehicle_data = [
            ('Truck-01', 'MH-12-AB-1001', 'truck', 5000, 45000, 2500000, 'North India'),
            ('Truck-02', 'MH-12-AB-1002', 'truck', 8000, 32000, 3200000, 'South India'),
            ('Truck-03', 'DL-01-CD-3003', 'truck', 6000, 28000, 2800000, 'North India'),
            ('Van-01', 'MH-14-EF-2001', 'van', 1500, 15000, 800000, 'West India'),
            ('Van-02', 'KA-01-GH-2002', 'van', 1200, 22000, 750000, 'South India'),
            ('Van-03', 'TN-01-IJ-2003', 'van', 1800, 18000, 900000, 'South India'),
            ('Van-04', 'GJ-01-KL-2004', 'van', 1000, 8000, 650000, 'West India'),
            ('Bike-01', 'MH-12-MN-3001', 'bike', 50, 5000, 120000, 'West India'),
            ('Bike-02', 'DL-01-OP-3002', 'bike', 30, 3200, 95000, 'East India'),
            ('Van-05', 'RJ-14-QR-2005', 'van', 500, 12000, 550000, 'North India'),
        ]
        vehicles = []
        for name, plate, vtype, cap, odo, cost, region in vehicle_data:
            v, _ = Vehicle.objects.get_or_create(
                license_plate=plate,
                defaults={
                    'name': name, 'vehicle_type': vtype,
                    'capacity': cap, 'odometer': odo,
                    'acquisition_cost': cost, 'region': region,
                }
            )
            vehicles.append(v)

        self.stdout.write(f'  ✅ {len(vehicle_data)} vehicles created')

        # ── Drivers ──
        driver_data = [
            ('Alex Johnson', 'DL-2024-001', date.today() + timedelta(days=365), 'van', 95.5),
            ('Maria Garcia', 'DL-2024-002', date.today() + timedelta(days=200), 'truck', 88.0),
            ('Raj Patel', 'DL-2024-003', date.today() + timedelta(days=30), 'van', 72.5),
            ('Sarah Khan', 'DL-2024-004', date.today() - timedelta(days=15), 'truck', 90.0),
            ('Vikram Singh', 'DL-2024-005', date.today() + timedelta(days=500), 'all', 97.0),
            ('Anita Desai', 'DL-2024-006', date.today() + timedelta(days=180), 'bike', 85.0),
            ('Mohammed Ali', 'DL-2024-007', date.today() + timedelta(days=400), 'van', 91.0),
            ('Deepa Nair', 'DL-2024-008', date.today() + timedelta(days=250), 'truck', 78.5),
        ]
        drivers = []
        for name, lic, expiry, cat, score in driver_data:
            d, _ = Driver.objects.get_or_create(
                license_number=lic,
                defaults={
                    'name': name, 'license_expiry': expiry,
                    'vehicle_category': cat, 'safety_score': score,
                }
            )
            drivers.append(d)

        sarah = Driver.objects.filter(license_number='DL-2024-004').first()
        if sarah:
            sarah.status = Driver.Status.SUSPENDED
            sarah.save()

        self.stdout.write(f'  ✅ {len(driver_data)} drivers created')

        # ── Completed Trips ──
        if not Trip.objects.exists():
            for i in range(12):
                v = random.choice(vehicles[:7])
                d = random.choice([d for d in drivers if d.is_license_valid and d.license_number != 'DL-2024-004'])
                origin, dest = random.sample(CITIES, 2)
                odo_start = float(v.odometer)
                distance = random.randint(100, 800)
                cargo = Decimal(str(random.randint(10, int(v.capacity * Decimal('0.9')))))
                revenue = Decimal(str(random.randint(5000, 50000)))

                Trip.objects.create(
                    vehicle=v, driver=d,
                    origin=origin, destination=dest,
                    cargo_weight=cargo, revenue=revenue,
                    status=Trip.Status.COMPLETED,
                    odometer_start=Decimal(str(odo_start)),
                    odometer_end=Decimal(str(odo_start + distance)),
                )

            Trip.objects.create(
                vehicle=vehicles[3], driver=drivers[0],
                origin='Jaipur', destination='Delhi',
                cargo_weight=800, revenue=15000,
                status=Trip.Status.DRAFT,
            )
            Trip.objects.create(
                vehicle=vehicles[4], driver=drivers[6],
                origin='Chennai', destination='Bangalore',
                cargo_weight=500, revenue=8000,
                status=Trip.Status.DRAFT,
            )

            self.stdout.write('  ✅ 14 trips created (12 completed, 2 drafts)')

        # ── Maintenance ──
        if not Maintenance.objects.exists():
            maint_records = [
                (vehicles[0], 'oil_change', 3500, date.today() - timedelta(days=30), True),
                (vehicles[1], 'tire_rotation', 8000, date.today() - timedelta(days=15), True),
                (vehicles[2], 'brake_service', 12000, date.today() - timedelta(days=5), False),
                (vehicles[5], 'inspection', 2000, date.today() - timedelta(days=2), False),
            ]
            for v, stype, cost, d, resolved in maint_records:
                Maintenance.objects.create(
                    vehicle=v, service_type=stype,
                    cost=cost, date=d, is_resolved=resolved,
                )
                if not resolved:
                    v.status = Vehicle.Status.IN_SHOP
                    v.save()

            self.stdout.write('  ✅ 4 maintenance records created')

        # ── Expenses ──
        if not Expense.objects.exists():
            for v in vehicles[:7]:
                for _ in range(random.randint(2, 5)):
                    liters = Decimal(str(random.randint(20, 200)))
                    cost = liters * Decimal(str(random.uniform(95, 115)))
                    Expense.objects.create(
                        vehicle=v,
                        category='fuel',
                        liters=liters,
                        cost=round(cost, 2),
                        date=date.today() - timedelta(days=random.randint(1, 60)),
                    )
            self.stdout.write('  ✅ Fuel expenses created')

        self.stdout.write(self.style.SUCCESS('\n🎉 Database seeded successfully!'))
        self.stdout.write(self.style.SUCCESS('   Login: admin / fleetflow123'))
        self.stdout.write(self.style.SUCCESS('   Roles: dispatcher1, safety1, analyst1 (same password)'))
