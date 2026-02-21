from django.contrib import admin
from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'category', 'cost', 'liters', 'date', 'trip')
    list_filter = ('category', 'date')
