from django.urls import path, re_path
from . import views

urlpatterns = [
    # Confirmed reservations endpoint
    path('reservation/confirm/', views.get_confirmed_reservations, name='get_confirmed_reservations'),
    re_path(r'^reservation/confirm/?$', views.get_confirmed_reservations, name='get_confirmed_reservations_no_slash'),

    # All reservations endpoint for calendar (regardless of status)
    path('reservation/all/', views.get_all_reservations_calendar, name='get_all_reservations_calendar'),
    re_path(r'^reservation/all/?$', views.get_all_reservations_calendar, name='get_all_reservations_calendar_no_slash'),

    # Payment endpoints (must come before booking/<uuid> patterns)
    path('booking/payment/', views.create_booking_payment, name='create_booking_payment'),
    path('booking/payment/<uuid:booking_id>/', views.update_booking_payment, name='update_booking_payment'),
    re_path(r'^booking/payment/(?P<booking_id>[0-9a-f-]{36})/?$', views.update_booking_payment, name='update_booking_payment_flexible'),

    # GET/PUT/DELETE booking endpoint - support both with and without trailing slash
    path('booking/<uuid:booking_id>/', views.get_booking, name='get_booking'),
    re_path(r'^booking/(?P<booking_id>[0-9a-f-]{36})/?$', views.get_booking, name='get_booking_flexible'),

    # Support both with and without trailing slash for booking endpoint
    path('booking/', views.create_booking, name='create_booking'),
    re_path(r'^booking/?$', views.create_booking, name='create_booking_no_slash'),

    # Basic data endpoint - get users and tours (must come before empty path)
    path('basic/', views.get_basic_data, name='get_basic_data'),
    re_path(r'^basic/?$', views.get_basic_data, name='get_basic_data_no_slash'),

    # Get all reservations endpoint - support both with and without trailing slash
    path('', views.get_all_reservations, name='get_all_reservations'),
    re_path(r'^$', views.get_all_reservations, name='get_all_reservations_no_slash'),

    # Public booking endpoint - accessible without authentication
    path('public/booking/<str:link>/', views.get_public_booking, name='get_public_booking'),
    re_path(r'^public/booking/(?P<link>.+)/?$', views.get_public_booking, name='get_public_booking_flexible'),
]
