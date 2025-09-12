from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:booking_id>/', views.delete_quote, name='delete_quote'),
]
