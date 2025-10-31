from django.urls import path, re_path
from . import views, logistics_views

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

    # Dashboard data endpoint
    path('dashboard/all-data/', views.get_dashboard_data, name='get_dashboard_data'),
    re_path(r'^dashboard/all-data/?$', views.get_dashboard_data, name='get_dashboard_data_no_slash'),

    # Booking tour action endpoints
    path('booking-tour/<uuid:tour_id>/cancel/', views.cancel_booking_tour, name='cancel_booking_tour'),
    path('booking-tour/<uuid:tour_id>/checkin/', views.checkin_booking_tour, name='checkin_booking_tour'),
    path('booking-tour/<uuid:tour_id>/noshow/', views.noshow_booking_tour, name='noshow_booking_tour'),
    path('booking-tour/<uuid:tour_id>/update/', views.update_booking_tour, name='update_booking_tour'),
    path('booking/<uuid:booking_id>/add-tour/', views.add_tour_to_booking, name='add_tour_to_booking'),

    # New Logistics/Operations endpoints
    path('<uuid:booking_id>/', logistics_views.update_reservation_logistics, name='update_reservation_logistics'),
    re_path(r'^(?P<booking_id>[0-9a-f-]{36})/?$', logistics_views.update_reservation_logistics, name='update_reservation_logistics_flexible'),
    path('<uuid:booking_id>/status/', logistics_views.update_reservation_status, name='update_reservation_status'),
    re_path(r'^(?P<booking_id>[0-9a-f-]{36})/status/?$', logistics_views.update_reservation_status, name='update_reservation_status_flexible'),
    path('filter-options/', logistics_views.get_filter_options, name='get_filter_options'),
    re_path(r'^filter-options/?$', logistics_views.get_filter_options, name='get_filter_options_flexible'),
    path('service-orders/', logistics_views.generate_service_orders, name='generate_service_orders'),
    re_path(r'^service-orders/?$', logistics_views.generate_service_orders, name='generate_service_orders_flexible'),
    path('send-confirmations/', logistics_views.send_confirmation_emails, name='send_confirmation_emails'),
    re_path(r'^send-confirmations/?$', logistics_views.send_confirmation_emails, name='send_confirmation_emails_flexible'),
]
