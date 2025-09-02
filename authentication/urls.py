from django.urls import path, re_path
from . import views

urlpatterns = [
    # Using re_path to handle both with and without trailing slash
    re_path(r'^signin/?$', views.signin, name='signin'),
    re_path(r'^signup/?$', views.signup, name='signup'),
    re_path(r'^signout/?$', views.signout, name='signout'),
    re_path(r'^forgot-password/?$', views.forgot_password, name='forgot-password'),
    re_path(r'^reset-password/?$', views.reset_password, name='reset-password'),
    re_path(r'^verify-email/?$', views.verify_email, name='verify-email'),
    re_path(r'^refresh-token/?$', views.refresh_token, name='refresh-token'),
    re_path(r'^google/?$', views.google_auth, name='google-auth'),
]
