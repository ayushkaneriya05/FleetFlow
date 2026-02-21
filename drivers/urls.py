from django.urls import path
from . import views

app_name = 'drivers'

urlpatterns = [
    path('', views.driver_list, name='driver_list'),
    path('add/', views.driver_create, name='driver_create'),
    path('<int:pk>/', views.driver_detail, name='driver_detail'),
    path('<int:pk>/edit/', views.driver_edit, name='driver_edit'),
    path('<int:pk>/status/<str:new_status>/', views.driver_toggle_status, name='driver_toggle_status'),
]
