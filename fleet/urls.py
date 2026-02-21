from django.urls import path
from . import views

app_name = 'fleet'

urlpatterns = [
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/add/', views.vehicle_create, name='vehicle_create'),
    path('vehicles/<int:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),
    path('vehicles/<int:pk>/toggle-retire/', views.vehicle_toggle_retire, name='vehicle_toggle_retire'),
    path('maintenance/', views.maintenance_list, name='maintenance_list'),
    path('maintenance/add/', views.maintenance_create, name='maintenance_create'),
    path('maintenance/<int:pk>/resolve/', views.maintenance_resolve, name='maintenance_resolve'),
]
