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
    
    # Delete booking endpoint - support both with and without trailing slash
    re_path(r'^booking/(?P<booking_id>[0-9a-f-]+)$', views.delete_booking, name='delete_booking_no_slash'),
    
    # Get all reservations endpoint - support both with and without trailing slash
    path('', views.get_all_reservations, name='get_all_reservations'),
    re_path(r'^$', views.get_all_reservations, name='get_all_reservations_no_slash'),
]
