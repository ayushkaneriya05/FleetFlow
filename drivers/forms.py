from django import forms
from .models import Driver

FORM_INPUT_CLASS = 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition text-sm'


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['name', 'license_number', 'license_expiry', 'vehicle_category', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'Full name'}),
            'license_number': forms.TextInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'License number'}),
            'license_expiry': forms.DateInput(attrs={'class': FORM_INPUT_CLASS, 'type': 'date'}),
            'vehicle_category': forms.Select(attrs={'class': FORM_INPUT_CLASS}),
            'phone': forms.TextInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'Phone number'}),
        }
