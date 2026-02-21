import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Trip
from .forms import TripCreateForm, TripCompleteForm
from .services import dispatch_trip, complete_trip, cancel_trip, TripValidationError
from core.decorators import role_required
from core.audit import log_creation


def _htmx_success_row(request, template, context, table_id, toast_msg, swap='afterbegin'):
    """On success: return a row partial retargeted to the table, close modal, show toast."""
    resp = render(request, template, context)
    resp['HX-Retarget'] = f'#{table_id}'
    resp['HX-Reswap'] = swap
    resp['HX-Trigger'] = json.dumps({
        'showToast': {'message': toast_msg, 'level': 'success'},
        'closeModal': True,
    })
    return resp


def _htmx_error_form(request, template, context):
    """On error: re-render the modal form partial (stays in modal)."""
    return render(request, template, context)


def _htmx_inline_toasts(request, template, context):
    """For inline HTMX actions (dispatch/cancel): return row + toast via HX-Trigger."""
    resp = render(request, template, context)
    toast_msgs = []
    storage = messages.get_messages(request)
    for m in storage:
        toast_msgs.append({'message': str(m), 'level': m.tags.split()[-1] if m.tags else 'info'})
    if toast_msgs:
        resp['HX-Trigger'] = json.dumps({'showToasts': toast_msgs})
    return resp


@login_required
def trip_list(request):
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '')
    trips = Trip.objects.select_related('vehicle', 'driver').all()
    if status_filter:
        trips = trips.filter(status=status_filter)
    if search:
        trips = trips.filter(origin__icontains=search) | trips.filter(destination__icontains=search)
    context = {
        'trips': trips,
        'statuses': Trip.Status.choices,
        'selected_status': status_filter,
        'search_query': search,
    }
    return render(request, 'operations/trip_list.html', context)


@login_required
@role_required('manager', 'dispatcher')
def trip_create(request):
    if request.method == 'POST':
        form = TripCreateForm(request.POST)
        if form.is_valid():
            trip = form.save()
            log_creation(trip, request.user, f'Trip {trip.origin} → {trip.destination}')
            if request.htmx:
                return _htmx_success_row(
                    request, 'operations/partials/trip_row.html', {'trip': trip},
                    'trip-table-body', f'Trip #{trip.pk} created as Draft.',
                )
            messages.success(request, f'Trip #{trip.pk} created as Draft.')
            return redirect('operations:trip_list')
        else:
            if request.htmx:
                return _htmx_error_form(request, 'operations/partials/trip_modal_form.html',
                                        {'form': form, 'title': 'Create Trip', 'action_url': request.path})
    else:
        form = TripCreateForm()
    template = 'operations/partials/trip_modal_form.html' if request.htmx else 'operations/trip_form.html'
    return render(request, template, {'form': form, 'title': 'Create Trip', 'action_url': request.path})


@login_required
@role_required('manager', 'dispatcher')
def trip_edit(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if trip.status != Trip.Status.DRAFT:
        messages.error(request, f'Trip #{trip.pk} cannot be edited (status: {trip.get_status_display()}).')
        return redirect('operations:trip_list')
    if request.method == 'POST':
        form = TripCreateForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            trip.refresh_from_db()
            if request.htmx:
                return _htmx_success_row(
                    request, 'operations/partials/trip_row.html', {'trip': trip},
                    f'trip-row-{trip.pk}', f'Trip #{trip.pk} updated.', swap='outerHTML',
                )
            messages.success(request, f'Trip #{trip.pk} updated.')
            return redirect('operations:trip_list')
        else:
            if request.htmx:
                return _htmx_error_form(request, 'operations/partials/trip_modal_form.html',
                                        {'form': form, 'title': f'Edit Trip #{trip.pk}', 'action_url': request.path})
    else:
        form = TripCreateForm(instance=trip)
    template = 'operations/partials/trip_modal_form.html' if request.htmx else 'operations/trip_form.html'
    return render(request, template, {'form': form, 'title': f'Edit Trip #{trip.pk}', 'action_url': request.path})


@login_required
@role_required('manager', 'dispatcher')
def trip_dispatch(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    try:
        dispatch_trip(trip, user=request.user)
        messages.success(request, f'Trip #{trip.pk} dispatched! Vehicle and driver assigned.')
    except TripValidationError as e:
        for error in e.args[0]:
            messages.error(request, error)

    if request.htmx:
        trip.refresh_from_db()
        return _htmx_inline_toasts(request, 'operations/partials/trip_row.html', {'trip': trip})
    return redirect('operations:trip_list')


@login_required
@role_required('manager', 'dispatcher')
def trip_complete(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == 'POST':
        form = TripCompleteForm(request.POST)
        if form.is_valid():
            try:
                complete_trip(trip, form.cleaned_data['odometer_end'], user=request.user)
                if request.htmx:
                    trip.refresh_from_db()
                    return _htmx_success_row(
                        request, 'operations/partials/trip_row.html', {'trip': trip},
                        f'trip-row-{trip.pk}', f'Trip #{trip.pk} completed!', swap='outerHTML',
                    )
                messages.success(request, f'Trip #{trip.pk} completed!')
                return redirect('operations:trip_list')
            except TripValidationError as e:
                for error in e.args[0]:
                    messages.error(request, error)
        if request.htmx:
            return _htmx_error_form(request, 'operations/partials/trip_complete_modal.html',
                                    {'form': form, 'trip': trip, 'action_url': request.path})
    else:
        form = TripCompleteForm()
    template = 'operations/partials/trip_complete_modal.html' if request.htmx else 'operations/trip_complete_form.html'
    return render(request, template, {'form': form, 'trip': trip, 'action_url': request.path})


@login_required
@role_required('manager', 'dispatcher')
def trip_cancel(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    try:
        cancel_trip(trip, user=request.user)
        messages.success(request, f'Trip #{trip.pk} cancelled.')
    except TripValidationError as e:
        for error in e.args[0]:
            messages.error(request, error)

    if request.htmx:
        trip.refresh_from_db()
        return _htmx_inline_toasts(request, 'operations/partials/trip_row.html', {'trip': trip})
    return redirect('operations:trip_list')


@login_required
def trip_detail(request, pk):
    trip = get_object_or_404(Trip.objects.select_related('vehicle', 'driver'), pk=pk)
    expenses = trip.expenses.all()
    context = {'trip': trip, 'expenses': expenses}
    return render(request, 'operations/trip_detail.html', context)
