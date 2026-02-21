from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Trip
from .forms import TripCreateForm, TripCompleteForm
from .services import dispatch_trip, complete_trip, cancel_trip, TripValidationError
from core.decorators import role_required
from core.audit import log_creation


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
            messages.success(request, f'Trip #{trip.pk} created as Draft.')
            if request.htmx:
                return render(request, 'operations/partials/trip_row.html', {'trip': trip})
            return redirect('operations:trip_list')
    else:
        form = TripCreateForm()
    template = 'operations/partials/trip_form.html' if request.htmx else 'operations/trip_form.html'
    return render(request, template, {'form': form, 'title': 'Create Trip'})


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
        return render(request, 'operations/partials/trip_row.html', {'trip': trip})
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
                messages.success(request, f'Trip #{trip.pk} completed!')
                if request.htmx:
                    trip.refresh_from_db()
                    return render(request, 'operations/partials/trip_row.html', {'trip': trip})
                return redirect('operations:trip_list')
            except TripValidationError as e:
                for error in e.args[0]:
                    messages.error(request, error)
    else:
        form = TripCompleteForm()
    template = 'operations/partials/trip_complete_form.html' if request.htmx else 'operations/trip_complete_form.html'
    return render(request, template, {'form': form, 'trip': trip})


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
        return render(request, 'operations/partials/trip_row.html', {'trip': trip})
    return redirect('operations:trip_list')


@login_required
def trip_detail(request, pk):
    trip = get_object_or_404(Trip.objects.select_related('vehicle', 'driver'), pk=pk)
    expenses = trip.expenses.all()
    context = {'trip': trip, 'expenses': expenses}
    return render(request, 'operations/trip_detail.html', context)
