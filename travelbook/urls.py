from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from customers.views import CustomerListCreateView, CustomerDetailView
from tours.views import TourListCreateView, TourDetailView
from settings_app.views import DestinationListCreateView, DestinationDetailView, SystemSettingsListCreateView, SystemSettingsDetailView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Endpoints
    path('api/auth/', include('authentication.urls')),
    path('api/users/', include('users.urls')),
    path('api/quotes/', include('quotes.urls')),
    path('api/tours/', include('tours.urls')),
    path('api/reservations/', include('reservations.urls')),
    path('api/', include('reservations.urls')),  # Direct booking endpoint
    path('api/customers/', include('customers.urls')),
    # Handle customers URL without trailing slash - direct view
    path('api/customers', CustomerListCreateView.as_view(), name='customers-no-slash'),
    # Handle customer detail URL without trailing slash
    path('api/customers/<uuid:pk>', CustomerDetailView.as_view(), name='customer-detail-no-slash'),
    # Handle tours URL without trailing slash - direct view
    path('api/tours', TourListCreateView.as_view(), name='tours-no-slash'),
    # Handle tour detail URL without trailing slash
    path('api/tours/<uuid:pk>', TourDetailView.as_view(), name='tour-detail-no-slash'),
    path('api/commissions/', include('commissions.urls')),
    path('api/logistics/', include('logistics.urls')),
    path('api/reports/', include('reports.urls')),
    # Handle settings destinations URL without trailing slash (must come before settings include)
    path('api/settings/destinations', DestinationListCreateView.as_view(), name='destinations-no-slash'),
    # Handle destination detail URL without trailing slash
    path('api/settings/destinations/<uuid:pk>', DestinationDetailView.as_view(), name='destination-detail-no-slash'),
    # Handle settings system URL without trailing slash
    path('api/settings/system', SystemSettingsListCreateView.as_view(), name='system-settings-no-slash'),
    # Handle system settings detail URL without trailing slash
    path('api/settings/system/<uuid:pk>', SystemSettingsDetailView.as_view(), name='system-settings-detail-no-slash'),
    path('api/settings/', include('settings_app.urls')),
    path('api/support/', include('support.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
