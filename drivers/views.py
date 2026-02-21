import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Driver
from .forms import DriverForm
from core.decorators import role_required
from core.audit import log_state_change, log_creation


def _htmx_success_row(request, template, context, table_id, toast_msg, swap='afterbegin'):
    resp = render(request, template, context)
    resp['HX-Retarget'] = f'#{table_id}'
    resp['HX-Reswap'] = swap
    resp['HX-Trigger'] = json.dumps({
        'showToast': {'message': toast_msg, 'level': 'success'},
        'closeModal': True,
    })
    return resp


def _htmx_error_form(request, template, context):
    return render(request, template, context)


def _htmx_inline_toasts(request, template, context):
    resp = render(request, template, context)
    toast_msgs = []
    storage = messages.get_messages(request)
    for m in storage:
        toast_msgs.append({'message': str(m), 'level': m.tags.split()[-1] if m.tags else 'info'})
    if toast_msgs:
        resp['HX-Trigger'] = json.dumps({'showToasts': toast_msgs})
    return resp


@login_required
def driver_list(request):
    status_filter = request.GET.get('status', '')
    category = request.GET.get('category', '')
    search = request.GET.get('q', '')

    drivers = Driver.objects.all()
    if status_filter:
        drivers = drivers.filter(status=status_filter)
    if category:
        drivers = drivers.filter(vehicle_category=category)
    if search:
        drivers = drivers.filter(name__icontains=search) | drivers.filter(license_number__icontains=search)

    context = {
        'drivers': drivers,
        'statuses': Driver.Status.choices,
        'categories': Driver.VehicleCategory.choices,
        'selected_status': status_filter,
        'selected_category': category,
        'search_query': search,
    }
    return render(request, 'drivers/driver_list.html', context)


@login_required
@role_required('manager', 'safety_officer')
def driver_create(request):
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            driver = form.save()
            log_creation(driver, request.user, f'Driver "{driver.name}" added')
            if request.htmx:
                return _htmx_success_row(
                    request, 'drivers/partials/driver_row.html', {'driver': driver},
                    'driver-table-body', f'Driver "{driver.name}" added.',
                )
            messages.success(request, f'Driver "{driver.name}" added successfully.')
            return redirect('drivers:driver_list')
        else:
            if request.htmx:
                return _htmx_error_form(request, 'drivers/partials/driver_modal_form.html',
                                        {'form': form, 'title': 'Add Driver', 'action_url': request.path})
    else:
        form = DriverForm()

    template = 'drivers/partials/driver_modal_form.html' if request.htmx else 'drivers/driver_form.html'
    return render(request, template, {'form': form, 'title': 'Add Driver', 'action_url': request.path})


@login_required
@role_required('manager', 'safety_officer')
def driver_edit(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            if request.htmx:
                return _htmx_success_row(
                    request, 'drivers/partials/driver_row.html', {'driver': driver},
                    'driver-table-body', f'Driver "{driver.name}" updated.',
                )
            messages.success(request, f'Driver "{driver.name}" updated.')
            return redirect('drivers:driver_list')
        else:
            if request.htmx:
                return _htmx_error_form(request, 'drivers/partials/driver_modal_form.html',
                                        {'form': form, 'title': 'Edit Driver', 'driver': driver, 'action_url': request.path})
    else:
        form = DriverForm(instance=driver)

    template = 'drivers/partials/driver_modal_form.html' if request.htmx else 'drivers/driver_form.html'
    return render(request, template, {'form': form, 'title': 'Edit Driver', 'driver': driver, 'action_url': request.path})


@login_required
@role_required('manager', 'safety_officer')
def driver_toggle_status(request, pk, new_status):
    driver = get_object_or_404(Driver, pk=pk)
    valid_statuses = dict(Driver.Status.choices)

    if new_status not in valid_statuses:
        messages.error(request, 'Invalid status.')
    elif driver.status == Driver.Status.ON_TRIP:
        messages.error(request, 'Cannot change status of a driver currently on a trip.')
    else:
        old = driver.status
        driver.status = new_status
        driver.save()
        log_state_change(driver, request.user, 'status', old, new_status, f'Status changed to {valid_statuses[new_status]}')
        messages.success(request, f'Driver "{driver.name}" status changed to {valid_statuses[new_status]}.')

    if request.htmx:
        return _htmx_inline_toasts(request, 'drivers/partials/driver_row.html', {'driver': driver})
    return redirect('drivers:driver_list')


@login_required
def driver_detail(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    trips = driver.trips.select_related('vehicle').order_by('-created_at')[:20]
    context = {
        'driver': driver,
        'trips': trips,
        'completion_rate': driver.trip_completion_rate,
    }
    return render(request, 'drivers/driver_detail.html', context)
