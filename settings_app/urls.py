from django.urls import path
from . import views

urlpatterns = [
    # Destinations endpoints
    path('destinations/', views.DestinationListCreateView.as_view(), name='destination-list-create'),
    path('destinations/<uuid:pk>/', views.DestinationDetailView.as_view(), name='destination-detail'),

    # System settings endpoints
    path('system/', views.SystemSettingsListCreateView.as_view(), name='system-settings-list-create'),
    path('system/<uuid:pk>/', views.SystemSettingsDetailView.as_view(), name='system-settings-detail'),

    # Vehicle endpoints
    path('vehicle/', views.VehicleListCreateView.as_view(), name='vehicle-list-create'),
    path('vehicle/<uuid:pk>/', views.VehicleDetailView.as_view(), name='vehicle-detail'),

    # New settings endpoints
    path('system/financial-config/', views.FinancialConfigListCreateView.as_view(), name='financial-config-list-create'),
    path('system/financial-config/<uuid:pk>/', views.FinancialConfigDetailView.as_view(), name='financial-config-detail'),

    path('system/payment-fee/', views.PaymentFeeListCreateView.as_view(), name='payment-fee-list-create'),
    path('system/payment-fee/<uuid:pk>/', views.PaymentFeeDetailView.as_view(), name='payment-fee-detail'),

    path('system/payment-account/', views.PaymentAccountListCreateView.as_view(), name='payment-account-list-create'),
    path('system/payment-account/<uuid:pk>/', views.PaymentAccountDetailView.as_view(), name='payment-account-detail'),

    path('system/terms/', views.TermsConfigListCreateView.as_view(), name='terms-config-list-create'),
    path('system/terms/<uuid:pk>/', views.TermsConfigDetailView.as_view(), name='terms-config-detail'),

    path('upload-terms/', views.upload_terms_file, name='upload-terms-file'),
]
