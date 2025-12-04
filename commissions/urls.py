from django.urls import path
from . import views

urlpatterns = [
    # Commission endpoints
    path('', views.CommissionListView.as_view(), name='commission-list'),
    path('unique-values/', views.commission_unique_values, name='commission-unique-values'),
    path('extended-unique-values/', views.extended_unique_values, name='extended-unique-values'),
    path('summary/', views.commission_summary, name='commission-summary'),
    path('close/', views.close_commissions, name='close-commissions'),

    # Operator payment endpoints
    path('operators/', views.OperatorPaymentListView.as_view(), name='operator-payment-list'),
    path('operators/unique-values/', views.operator_unique_values, name='operator-unique-values'),
    path('operators/summary/', views.operator_summary, name='operator-summary'),
    path('operators/close/', views.close_operator_payments, name='close-operator-payments'),

    # Closing endpoints
    path('closings/', views.ClosingListView.as_view(), name='closing-list'),
    path('closings/<uuid:closing_id>/', views.closing_detail, name='closing-detail'),
    path('closings/<uuid:closing_id>/undo/', views.undo_closing, name='undo-closing'),
]
