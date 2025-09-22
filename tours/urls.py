from django.urls import path
from . import views

urlpatterns = [
    path('', views.TourListCreateView.as_view(), name='tour-list-create'),
    path('<uuid:pk>/', views.TourDetailView.as_view(), name='tour-detail'),
]
