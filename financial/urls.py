from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'expenses', views.ExpenseViewSet, basename='expense')
router.register(r'transfers', views.BankTransferViewSet, basename='transfer')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.financial_dashboard, name='financial-dashboard'),
    path('receivables/', views.receivables_list, name='receivables-list'),
    path('payables/', views.payables_list, name='payables-list'),
    path('bank-statement/', views.bank_statement, name='bank-statement'),
]
