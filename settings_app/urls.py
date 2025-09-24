from django.urls import path
from . import views

urlpatterns = [
    # Destinations endpoints
    path('destinations/', views.DestinationListCreateView.as_view(), name='destination-list-create'),
    path('destinations/<uuid:pk>/', views.DestinationDetailView.as_view(), name='destination-detail'),

    # System settings endpoints
    path('system/', views.SystemSettingsListCreateView.as_view(), name='system-settings-list-create'),
    path('system/<uuid:pk>/', views.SystemSettingsDetailView.as_view(), name='system-settings-detail'),

    # Vehicle endpoints
    path('vehicle/', views.VehicleListCreateView.as_view(), name='vehicle-list-create'),
]
