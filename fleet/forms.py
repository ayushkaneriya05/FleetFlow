from django import forms
from .models import Vehicle, Maintenance

FORM_INPUT_CLASS = 'form-input'
FORM_SELECT_CLASS = FORM_INPUT_CLASS


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['name', 'license_plate', 'vehicle_type', 'capacity', 'odometer', 'acquisition_cost', 'region']
        widgets = {
            'name': forms.TextInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'e.g. Van-05'}),
            'license_plate': forms.TextInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'e.g. MH-12-AB-1234'}),
            'vehicle_type': forms.Select(attrs={'class': FORM_SELECT_CLASS}),
            'capacity': forms.NumberInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'Max capacity in kg', 'min': '0.01', 'step': '0.01'}),
            'odometer': forms.NumberInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'Current km', 'min': '0', 'step': '0.01'}),
            'acquisition_cost': forms.NumberInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'Cost in ₹', 'min': '0', 'step': '0.01'}),
            'region': forms.TextInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'e.g. North India'}),
        }


class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = Maintenance
        fields = ['vehicle', 'service_type', 'description', 'cost', 'date']
        widgets = {
            'vehicle': forms.Select(attrs={'class': FORM_SELECT_CLASS}),
            'service_type': forms.Select(attrs={'class': FORM_SELECT_CLASS}),
            'description': forms.Textarea(attrs={'class': FORM_INPUT_CLASS, 'rows': 3, 'placeholder': 'Service details...'}),
            'cost': forms.NumberInput(attrs={'class': FORM_INPUT_CLASS, 'min': '0', 'step': '0.01'}),
            'date': forms.DateInput(attrs={'class': FORM_INPUT_CLASS, 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.exclude(status=Vehicle.Status.RETIRED)
