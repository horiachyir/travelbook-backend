from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'operators', views.TourOperatorViewSet, basename='tour-operator')

urlpatterns = [
    path('', views.TourListCreateView.as_view(), name='tour-list-create'),
    path('<uuid:pk>/', views.TourDetailView.as_view(), name='tour-detail'),
    path('', include(router.urls)),
]
