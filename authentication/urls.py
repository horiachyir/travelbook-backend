from django.urls import path
from . import views

urlpatterns = [
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('signout/', views.signout, name='signout'),
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('reset-password/', views.reset_password, name='reset-password'),
    path('verify-email/', views.verify_email, name='verify-email'),
    path('refresh-token/', views.refresh_token, name='refresh-token'),
    path('google/', views.google_auth, name='google-auth'),
]
