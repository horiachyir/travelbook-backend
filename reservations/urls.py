from django.urls import path, re_path
from . import views

urlpatterns = [
    # Support both with and without trailing slash for booking endpoint
    path('booking/', views.create_booking, name='create_booking'),
    re_path(r'^booking$', views.create_booking, name='create_booking_no_slash'),
    
    # Payment endpoint
    path('booking/payment/', views.create_booking_payment, name='create_booking_payment'),
    
    path('bookings/', views.get_bookings, name='get_bookings'),
    path('booking/<uuid:booking_id>/', views.get_booking, name='get_booking'),
]
