from django.urls import path
from .views import BasicDataView

urlpatterns = [
    path('basic/', BasicDataView.as_view(), name='logistics-basic'),
]
