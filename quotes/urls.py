from django.urls import path, re_path
from . import views

urlpatterns = [
    # Support both with and without trailing slash
    path('<uuid:booking_id>/', views.delete_quote, name='delete_quote'),
    re_path(r'^(?P<booking_id>[0-9a-f-]+)$', views.delete_quote, name='delete_quote_no_slash'),
]
