from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Vehicle, Maintenance
from .forms import VehicleForm, MaintenanceForm
from core.decorators import role_required
from core.audit import log_state_change, log_creation


@login_required
def vehicle_list(request):
    """Page 3: Vehicle Registry."""
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('vehicle_type', '')
    search = request.GET.get('q', '')

    vehicles = Vehicle.objects.all()
    if status_filter:
        vehicles = vehicles.filter(status=status_filter)
    if type_filter:
        vehicles = vehicles.filter(vehicle_type=type_filter)
    if search:
        vehicles = vehicles.filter(name__icontains=search) | vehicles.filter(license_plate__icontains=search)

    context = {
        'vehicles': vehicles,
        'vehicle_types': Vehicle.VehicleType.choices,
        'statuses': Vehicle.Status.choices,
        'selected_status': status_filter,
        'selected_type': type_filter,
        'search_query': search,
    }
    return render(request, 'fleet/vehicle_list.html', context)


@login_required
@role_required('manager')
def vehicle_create(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save()
            log_creation(vehicle, request.user, f'Vehicle "{vehicle.name}" added to fleet')
            messages.success(request, f'Vehicle "{vehicle.name}" added successfully.')
            if request.htmx:
                return render(request, 'fleet/partials/vehicle_row.html', {'vehicle': vehicle})
            return redirect('fleet:vehicle_list')
    else:
        form = VehicleForm()

    template = 'fleet/partials/vehicle_form.html' if request.htmx else 'fleet/vehicle_form.html'
    return render(request, template, {'form': form, 'title': 'Add Vehicle'})


@login_required
@role_required('manager')
def vehicle_edit(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, f'Vehicle "{vehicle.name}" updated.')
            if request.htmx:
                return render(request, 'fleet/partials/vehicle_row.html', {'vehicle': vehicle})
            return redirect('fleet:vehicle_list')
    else:
        form = VehicleForm(instance=vehicle)

    template = 'fleet/partials/vehicle_form.html' if request.htmx else 'fleet/vehicle_form.html'
    return render(request, template, {'form': form, 'title': 'Edit Vehicle', 'vehicle': vehicle})


@login_required
@role_required('manager')
def vehicle_toggle_retire(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if vehicle.status == Vehicle.Status.ON_TRIP:
        messages.error(request, 'Cannot retire a vehicle that is currently on a trip.')
    elif vehicle.status == Vehicle.Status.IN_SHOP:
        messages.error(request, 'Cannot retire a vehicle that is currently in maintenance.')
    elif vehicle.status == Vehicle.Status.RETIRED:
        old = vehicle.status
        vehicle.status = Vehicle.Status.AVAILABLE
        vehicle.save()
        log_state_change(vehicle, request.user, 'status', old, vehicle.status, 'Vehicle reactivated')
        messages.success(request, f'Vehicle "{vehicle.name}" reactivated.')
    else:
        old = vehicle.status
        vehicle.status = Vehicle.Status.RETIRED
        vehicle.save()
        log_state_change(vehicle, request.user, 'status', old, vehicle.status, 'Vehicle retired')
        messages.success(request, f'Vehicle "{vehicle.name}" retired.')

    if request.htmx:
        return render(request, 'fleet/partials/vehicle_row.html', {'vehicle': vehicle})
    return redirect('fleet:vehicle_list')


# ── Maintenance Views ──

@login_required
def maintenance_list(request):
    """Page 5: Maintenance & Service Logs."""
    records = Maintenance.objects.select_related('vehicle').all()
    resolved = request.GET.get('resolved', '')
    if resolved == 'yes':
        records = records.filter(is_resolved=True)
    elif resolved == 'no':
        records = records.filter(is_resolved=False)

    context = {
        'records': records,
        'selected_resolved': resolved,
    }
    return render(request, 'fleet/maintenance_list.html', context)


@login_required
@role_required('manager', 'safety_officer')
def maintenance_create(request):
    if request.method == 'POST':
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                record = form.save()
                vehicle = record.vehicle
                old_status = vehicle.status
                if vehicle.status == Vehicle.Status.AVAILABLE:
                    vehicle.status = Vehicle.Status.IN_SHOP
                    vehicle.save()
                    log_state_change(vehicle, request.user, 'status', old_status, vehicle.status, f'Moved to shop for {record.get_service_type_display()}')
                log_creation(record, request.user, f'Maintenance record: {record.get_service_type_display()}')
            messages.success(request, f'Maintenance logged for "{vehicle.name}".')
            if request.htmx:
                return render(request, 'fleet/partials/maintenance_row.html', {'record': record})
            return redirect('fleet:maintenance_list')
    else:
        form = MaintenanceForm()

    template = 'fleet/partials/maintenance_form.html' if request.htmx else 'fleet/maintenance_form.html'
    return render(request, template, {'form': form, 'title': 'Log Maintenance'})


@login_required
@role_required('manager', 'safety_officer')
def maintenance_resolve(request, pk):
    record = get_object_or_404(Maintenance, pk=pk)
    if not record.is_resolved:
        with transaction.atomic():
            record.is_resolved = True
            record.save()
            vehicle = record.vehicle
            other_open = Maintenance.objects.filter(vehicle=vehicle, is_resolved=False).exclude(pk=pk).exists()
            if not other_open and vehicle.status == Vehicle.Status.IN_SHOP:
                old = vehicle.status
                vehicle.status = Vehicle.Status.AVAILABLE
                vehicle.save()
                log_state_change(vehicle, request.user, 'status', old, vehicle.status, 'All maintenance resolved')
        messages.success(request, f'Maintenance for "{vehicle.name}" marked as resolved.')
    if request.htmx:
        return render(request, 'fleet/partials/maintenance_row.html', {'record': record})
    return redirect('fleet:maintenance_list')
