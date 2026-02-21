import csv
from decimal import Decimal
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, F, Value
from django.db.models.functions import Coalesce
from fleet.models import Vehicle
from operations.models import Trip
from finance.models import Expense


@login_required
def analytics_dashboard(request):
    """Page 8: Operational Analytics & Financial Reports."""
    vehicle_type = request.GET.get('vehicle_type', '')
    region = request.GET.get('region', '')

    vehicles = Vehicle.objects.exclude(status=Vehicle.Status.RETIRED)
    if vehicle_type:
        vehicles = vehicles.filter(vehicle_type=vehicle_type)
    if region:
        vehicles = vehicles.filter(region__icontains=region)

    total_vehicles = vehicles.count()
    on_trip = vehicles.filter(status=Vehicle.Status.ON_TRIP).count()
    utilization = round((on_trip / total_vehicles * 100), 1) if total_vehicles > 0 else 0

    total_revenue = Trip.objects.filter(status=Trip.Status.COMPLETED).aggregate(s=Coalesce(Sum('revenue'), Value(Decimal('0'))))['s']
    total_fuel_cost = Expense.objects.filter(category='fuel').aggregate(s=Coalesce(Sum('cost'), Value(Decimal('0'))))['s']
    total_maintenance_cost = Expense.objects.filter(category='other').aggregate(s=Coalesce(Sum('cost'), Value(Decimal('0'))))['s']
    from fleet.models import Maintenance
    total_maint = Maintenance.objects.aggregate(s=Coalesce(Sum('cost'), Value(Decimal('0'))))['s']
    total_operational_cost = total_fuel_cost + total_maint

    # Per-vehicle analytics
    vehicle_analytics = []
    for v in vehicles:
        completed = Trip.objects.filter(vehicle=v, status=Trip.Status.COMPLETED)
        trips_with_distance = completed.exclude(odometer_start=None).exclude(odometer_end=None)
        total_distance = sum([float(t.odometer_end - t.odometer_start) for t in trips_with_distance])
        revenue = completed.aggregate(s=Coalesce(Sum('revenue'), Value(Decimal('0'))))['s']
        fuel_cost = Expense.objects.filter(vehicle=v, category='fuel').aggregate(s=Coalesce(Sum('cost'), Value(Decimal('0'))))['s']
        fuel_liters = Expense.objects.filter(vehicle=v, category='fuel').aggregate(s=Coalesce(Sum('liters'), Value(Decimal('0'))))['s']
        maint_cost = v.maintenance_records.aggregate(s=Coalesce(Sum('cost'), Value(Decimal('0'))))['s']
        total_cost = fuel_cost + maint_cost
        profit = revenue - total_cost

        fuel_efficiency = round(total_distance / float(fuel_liters), 1) if fuel_liters and fuel_liters > 0 else 0
        roi = round(float(profit) / float(total_cost) * 100, 1) if total_cost > 0 else 0

        vehicle_analytics.append({
            'vehicle': v,
            'total_distance': round(total_distance, 1),
            'total_liters': fuel_liters,
            'fuel_efficiency': fuel_efficiency,
            'revenue': revenue,
            'fuel_cost': fuel_cost,
            'maintenance_cost': maint_cost,
            'profit': profit,
            'roi': roi,
        })

    regions = Vehicle.objects.exclude(region='').values_list('region', flat=True).distinct().order_by('region')

    context = {
        'utilization': utilization,
        'total_revenue': total_revenue,
        'total_fuel_cost': total_fuel_cost,
        'total_operational_cost': total_operational_cost,
        'vehicle_analytics': vehicle_analytics,
        'vehicle_types': Vehicle.VehicleType.choices,
        'regions': regions,
        'selected_vehicle_type': vehicle_type,
        'selected_region': region,
    }
    return render(request, 'analytics/dashboard.html', context)


@login_required
def export_csv(request):
    """Export analytics data as CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="fleetflow_analytics.csv"'
    writer = csv.writer(response)
    writer.writerow(['Vehicle', 'Type', 'Region', 'Total Distance (km)', 'Fuel (L)', 'Efficiency (km/L)', 'Revenue', 'Fuel Cost', 'Maintenance Cost', 'Profit', 'ROI (%)'])

    for v in Vehicle.objects.exclude(status=Vehicle.Status.RETIRED):
        completed = Trip.objects.filter(vehicle=v, status=Trip.Status.COMPLETED)
        trips_with_distance = completed.exclude(odometer_start=None).exclude(odometer_end=None)
        total_distance = sum([float(t.odometer_end - t.odometer_start) for t in trips_with_distance])
        revenue = completed.aggregate(s=Coalesce(Sum('revenue'), Value(Decimal('0'))))['s']
        fuel_cost = Expense.objects.filter(vehicle=v, category='fuel').aggregate(s=Coalesce(Sum('cost'), Value(Decimal('0'))))['s']
        fuel_liters = Expense.objects.filter(vehicle=v, category='fuel').aggregate(s=Coalesce(Sum('liters'), Value(Decimal('0'))))['s']
        maint_cost = v.maintenance_records.aggregate(s=Coalesce(Sum('cost'), Value(Decimal('0'))))['s']
        total_cost = fuel_cost + maint_cost
        profit = revenue - total_cost
        fuel_efficiency = round(total_distance / float(fuel_liters), 1) if fuel_liters and fuel_liters > 0 else 0
        roi = round(float(profit) / float(total_cost) * 100, 1) if total_cost > 0 else 0

        writer.writerow([v.name, v.get_vehicle_type_display(), v.region, round(total_distance, 1), fuel_liters, fuel_efficiency, revenue, fuel_cost, maint_cost, profit, roi])

    return response
