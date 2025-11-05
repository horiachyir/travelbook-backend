from django.urls import path, re_path
from . import views

urlpatterns = [
    # Accept terms endpoint (must come before UUID pattern)
    path('share/<str:link>/accept/', views.accept_quote_terms, name='accept_quote_terms'),
    re_path(r'^share/(?P<link>[^/]+)/accept/?$', views.accept_quote_terms, name='accept_quote_terms_flexible'),

    # Support both with and without trailing slash for delete
    path('<uuid:booking_id>/', views.delete_quote, name='delete_quote'),
    re_path(r'^(?P<booking_id>[0-9a-f-]+)$', views.delete_quote, name='delete_quote_no_slash'),
]
