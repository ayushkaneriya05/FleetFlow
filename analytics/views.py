import csv
from decimal import Decimal
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, F, Value, Count
from django.db.models.functions import Coalesce
from fleet.models import Vehicle, Maintenance
from operations.models import Trip
from finance.models import Expense
from core.decorators import role_required


def _vehicle_stats(vehicle):
    """Compute per-vehicle analytics (shared by dashboard & CSV)."""
    completed = Trip.objects.filter(vehicle=vehicle, status=Trip.Status.COMPLETED)
    trips_with_distance = completed.exclude(odometer_start=None).exclude(odometer_end=None)
    total_distance = sum(float(t.odometer_end - t.odometer_start) for t in trips_with_distance)
    revenue = completed.aggregate(s=Coalesce(Sum('revenue'), Value(Decimal('0'))))['s']
    fuel_cost = Expense.objects.filter(vehicle=vehicle, category='fuel').aggregate(s=Coalesce(Sum('cost'), Value(Decimal('0'))))['s']
    fuel_liters = Expense.objects.filter(vehicle=vehicle, category='fuel').aggregate(s=Coalesce(Sum('liters'), Value(Decimal('0'))))['s']
    maint_cost = vehicle.maintenance_records.aggregate(s=Coalesce(Sum('cost'), Value(Decimal('0'))))['s']
    total_cost = fuel_cost + maint_cost
    profit = revenue - total_cost
    fuel_efficiency = round(total_distance / float(fuel_liters), 1) if fuel_liters and fuel_liters > 0 else 0
    roi = round(float(profit) / float(total_cost) * 100, 1) if total_cost > 0 else 0
    trip_count = completed.count()

    return {
        'vehicle': vehicle,
        'total_distance': round(total_distance, 1),
        'total_liters': fuel_liters,
        'fuel_efficiency': fuel_efficiency,
        'revenue': revenue,
        'fuel_cost': fuel_cost,
        'maintenance_cost': maint_cost,
        'total_cost': total_cost,
        'profit': profit,
        'roi': roi,
        'trip_count': trip_count,
    }


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

    # Per-vehicle analytics (filtered)
    vehicle_analytics = [_vehicle_stats(v) for v in vehicles]

    # ── Aggregate KPIs from filtered vehicles ──
    total_revenue = sum(v['revenue'] for v in vehicle_analytics)
    total_fuel_cost = sum(v['fuel_cost'] for v in vehicle_analytics)
    total_maint_cost = sum(v['maintenance_cost'] for v in vehicle_analytics)
    total_operational_cost = total_fuel_cost + total_maint_cost
    total_profit = total_revenue - total_operational_cost
    total_trips = sum(v['trip_count'] for v in vehicle_analytics)
    total_distance = sum(v['total_distance'] for v in vehicle_analytics)
    total_liters = sum(float(v['total_liters'] or 0) for v in vehicle_analytics)
    avg_efficiency = round(total_distance / total_liters, 1) if total_liters > 0 else 0

    # ── Fleet breakdown by type (for filtered vehicles) ──
    vehicle_ids = [v.pk for v in vehicles]
    type_breakdown = (
        Vehicle.objects.filter(pk__in=vehicle_ids)
        .values('vehicle_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    for item in type_breakdown:
        item['label'] = dict(Vehicle.VehicleType.choices).get(item['vehicle_type'], item['vehicle_type'])
        item['pct'] = round(item['count'] / total_vehicles * 100) if total_vehicles else 0

    # ── Top 5 vehicles by revenue ──
    top_revenue = sorted(vehicle_analytics, key=lambda x: x['revenue'], reverse=True)[:5]

    # ── Top 5 vehicles by profit ──
    top_profit = sorted(vehicle_analytics, key=lambda x: x['profit'], reverse=True)[:5]

    # ── Cost breakdown for bar chart (Revenue vs Fuel vs Maintenance) per vehicle ──
    chart_vehicles = sorted(vehicle_analytics, key=lambda x: x['revenue'], reverse=True)[:8]
    max_revenue = max((float(v['revenue']) for v in chart_vehicles), default=1) or 1

    regions = Vehicle.objects.exclude(region='').values_list('region', flat=True).distinct().order_by('region')

    context = {
        # KPI cards (filtered)
        'utilization': utilization,
        'total_revenue': total_revenue,
        'total_fuel_cost': total_fuel_cost,
        'total_operational_cost': total_operational_cost,
        'total_profit': total_profit,
        'total_trips': total_trips,
        'total_distance': round(total_distance, 1),
        'avg_efficiency': avg_efficiency,
        'total_vehicles_filtered': total_vehicles,
        # Visualizations
        'type_breakdown': type_breakdown,
        'top_revenue': top_revenue,
        'top_profit': top_profit,
        'chart_vehicles': chart_vehicles,
        'max_revenue': max_revenue,
        # Table
        'vehicle_analytics': vehicle_analytics,
        # Filters
        'vehicle_types': Vehicle.VehicleType.choices,
        'regions': regions,
        'selected_vehicle_type': vehicle_type,
        'selected_region': region,
    }
    return render(request, 'analytics/dashboard.html', context)


@login_required
@role_required('manager', 'analyst')
def export_csv(request):
    """Export analytics data as CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="fleetflow_analytics.csv"'
    writer = csv.writer(response)
    writer.writerow(['Vehicle', 'Type', 'Region', 'Trips', 'Total Distance (km)', 'Fuel (L)', 'Efficiency (km/L)', 'Revenue', 'Fuel Cost', 'Maintenance Cost', 'Profit', 'ROI (%)'])

    for v in Vehicle.objects.exclude(status=Vehicle.Status.RETIRED):
        stats = _vehicle_stats(v)
        writer.writerow([
            v.name, v.get_vehicle_type_display(), v.region,
            stats['trip_count'], stats['total_distance'], stats['total_liters'],
            stats['fuel_efficiency'], stats['revenue'], stats['fuel_cost'],
            stats['maintenance_cost'], stats['profit'], stats['roi'],
        ])

    return response
