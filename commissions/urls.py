from django.urls import path
from . import views

urlpatterns = [
    path('', views.CommissionListView.as_view(), name='commission-list'),
    path('unique-values/', views.commission_unique_values, name='commission-unique-values'),
    path('summary/', views.commission_summary, name='commission-summary'),
]
