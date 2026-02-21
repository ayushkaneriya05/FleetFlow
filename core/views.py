from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum, F
from django.utils import timezone
from fleet.models import Vehicle, Maintenance
from drivers.models import Driver
from operations.models import Trip


@login_required
def dashboard(request):
    """Command Center — High-level fleet oversight."""
    vehicle_type = request.GET.get('vehicle_type', '')
    region = request.GET.get('region', '')

    vehicles = Vehicle.objects.exclude(status=Vehicle.Status.RETIRED)

    if vehicle_type:
        vehicles = vehicles.filter(vehicle_type=vehicle_type)
    if region:
        vehicles = vehicles.filter(region__icontains=region)

    total_vehicles = vehicles.count()
    available_count = vehicles.filter(status=Vehicle.Status.AVAILABLE).count()
    on_trip_count = vehicles.filter(status=Vehicle.Status.ON_TRIP).count()
    in_maintenance_count = vehicles.filter(status=Vehicle.Status.IN_SHOP).count()
    utilization_rate = round((on_trip_count / total_vehicles * 100), 1) if total_vehicles > 0 else 0

    # Filter pending cargo by the same vehicle set
    vehicle_ids = vehicles.values_list('id', flat=True)
    pending_cargo = Trip.objects.filter(status=Trip.Status.DRAFT, vehicle_id__in=vehicle_ids).count()

    recent_trips = (
        Trip.objects.select_related('vehicle', 'driver')
        .filter(vehicle_id__in=vehicle_ids)
        .order_by('-updated_at')[:10]
    )

    regions = Vehicle.objects.exclude(region='').values_list('region', flat=True).distinct().order_by('region')

    context = {
        'total_vehicles': total_vehicles,
        'available_count': available_count,
        'on_trip_count': on_trip_count,
        'in_maintenance_count': in_maintenance_count,
        'utilization_rate': utilization_rate,
        'pending_cargo': pending_cargo,
        'recent_trips': recent_trips,
        'vehicle_types': Vehicle.VehicleType.choices,
        'regions': regions,
        'selected_vehicle_type': vehicle_type,
        'selected_region': region,
    }
    return render(request, 'core/dashboard.html', context)
