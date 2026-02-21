from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('core.urls')),
    path('fleet/', include('fleet.urls')),
    path('drivers/', include('drivers.urls')),
    path('operations/', include('operations.urls')),
    path('finance/', include('finance.urls')),
    path('analytics/', include('analytics.urls')),
]
