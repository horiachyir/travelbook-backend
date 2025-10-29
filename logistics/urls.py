from django.urls import path
from .views import BasicDataView, TourPassengerView

urlpatterns = [
    path('basic/', BasicDataView.as_view(), name='logistics-basic'),
    path('tours/passenger/', TourPassengerView.as_view(), name='logistics-tour-passenger'),
]
