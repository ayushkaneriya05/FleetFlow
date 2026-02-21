from django import forms
from .models import Expense
from fleet.models import Vehicle
from operations.models import Trip

FORM_INPUT_CLASS = 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition text-sm'


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['vehicle', 'trip', 'category', 'cost', 'liters', 'date', 'notes']
        widgets = {
            'vehicle': forms.Select(attrs={'class': FORM_INPUT_CLASS}),
            'trip': forms.Select(attrs={'class': FORM_INPUT_CLASS}),
            'category': forms.Select(attrs={'class': FORM_INPUT_CLASS}),
            'cost': forms.NumberInput(attrs={'class': FORM_INPUT_CLASS, 'min': '0', 'step': '0.01', 'placeholder': 'Amount in ₹'}),
            'liters': forms.NumberInput(attrs={'class': FORM_INPUT_CLASS, 'min': '0', 'step': '0.01', 'placeholder': 'Liters (fuel only)'}),
            'date': forms.DateInput(attrs={'class': FORM_INPUT_CLASS, 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': FORM_INPUT_CLASS, 'rows': 2, 'placeholder': 'Notes...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['trip'].required = False
        self.fields['trip'].queryset = Trip.objects.filter(status__in=['dispatched', 'completed'])
        self.fields['vehicle'].queryset = Vehicle.objects.exclude(status=Vehicle.Status.RETIRED)
