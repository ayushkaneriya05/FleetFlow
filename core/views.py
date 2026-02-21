from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum, F
from django.utils import timezone
from fleet.models import Vehicle, Maintenance
from drivers.models import Driver
from operations.models import Trip


@login_required
def dashboard(request):
    """Command Center — Page 2: High-level fleet oversight."""
    vehicle_type = request.GET.get('vehicle_type', '')
    status_filter = request.GET.get('status', '')
    region = request.GET.get('region', '')

    vehicles = Vehicle.objects.exclude(status=Vehicle.Status.RETIRED)

    if vehicle_type:
        vehicles = vehicles.filter(vehicle_type=vehicle_type)
    if region:
        vehicles = vehicles.filter(region__icontains=region)

    total_vehicles = vehicles.count()
    active_fleet = vehicles.filter(status=Vehicle.Status.ON_TRIP).count()
    maintenance_alerts = vehicles.filter(status=Vehicle.Status.IN_SHOP).count()
    available_count = vehicles.filter(status=Vehicle.Status.AVAILABLE).count()
    utilization_rate = round((active_fleet / total_vehicles * 100), 1) if total_vehicles > 0 else 0

    pending_cargo = Trip.objects.filter(status=Trip.Status.DRAFT).count()

    recent_trips = Trip.objects.select_related('vehicle', 'driver').order_by('-updated_at')[:10]

    regions = Vehicle.objects.exclude(region='').values_list('region', flat=True).distinct().order_by('region')

    context = {
        'total_vehicles': total_vehicles,
        'active_fleet': active_fleet,
        'maintenance_alerts': maintenance_alerts,
        'available_count': available_count,
        'utilization_rate': utilization_rate,
        'pending_cargo': pending_cargo,
        'recent_trips': recent_trips,
        'vehicle_types': Vehicle.VehicleType.choices,
        'regions': regions,
        'selected_vehicle_type': vehicle_type,
        'selected_region': region,
    }
    return render(request, 'core/dashboard.html', context)
