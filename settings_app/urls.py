from django.urls import path
from . import views

urlpatterns = [
    # Destinations endpoints
    path('destinations/', views.DestinationListCreateView.as_view(), name='destination-list-create'),
    path('destinations/<uuid:pk>/', views.DestinationDetailView.as_view(), name='destination-detail'),
]
