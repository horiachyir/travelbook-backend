from django.urls import path
from . import views

urlpatterns = [
    path('booking/', views.create_booking, name='create_booking'),
    path('bookings/', views.get_bookings, name='get_bookings'),
    path('booking/<uuid:booking_id>/', views.get_booking, name='get_booking'),
]
