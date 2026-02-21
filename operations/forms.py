from django import forms
from .models import Trip
from fleet.models import Vehicle
from drivers.models import Driver

FORM_INPUT_CLASS = 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition text-sm'


class TripCreateForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['vehicle', 'driver', 'origin', 'destination', 'cargo_weight', 'revenue', 'notes']
        widgets = {
            'vehicle': forms.Select(attrs={'class': FORM_INPUT_CLASS}),
            'driver': forms.Select(attrs={'class': FORM_INPUT_CLASS}),
            'origin': forms.TextInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'Origin city/warehouse'}),
            'destination': forms.TextInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'Destination city/warehouse'}),
            'cargo_weight': forms.NumberInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'Weight in kg', 'min': '0.01', 'step': '0.01'}),
            'revenue': forms.NumberInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'Revenue in ₹', 'min': '0', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': FORM_INPUT_CLASS, 'rows': 2, 'placeholder': 'Additional notes...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.filter(status=Vehicle.Status.AVAILABLE)
        self.fields['driver'].queryset = Driver.objects.filter(status=Driver.Status.AVAILABLE)


class TripCompleteForm(forms.Form):
    odometer_end = forms.DecimalField(
        max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': FORM_INPUT_CLASS,
            'placeholder': 'Final odometer reading in km',
            'min': '0', 'step': '0.01',
        }),
    )
