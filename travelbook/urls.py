from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/users/', include('users.urls')),
    path('api/quotes/', include('quotes.urls')),
    path('api/tours/', include('tours.urls')),
    path('api/reservations/', include('reservations.urls')),
    path('api/customers/', include('customers.urls')),
    path('api/commissions/', include('commissions.urls')),
    path('api/logistics/', include('logistics.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/settings/', include('settings_app.urls')),
    path('api/support/', include('support.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
