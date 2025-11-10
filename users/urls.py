from django.urls import path
from . import views

urlpatterns = [
    path('', views.UserListCreateView.as_view(), name='user-list-create'),
    path('<uuid:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    # Operators endpoint
    path('operator/', views.get_operators, name='get-operators'),
    path('operator', views.get_operators, name='get-operators-no-slash'),
    # Profile endpoints (with trailing slash)
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/avatar/', views.update_avatar, name='update-avatar'),
    # Profile endpoints (without trailing slash)
    path('profile', views.UserProfileView.as_view(), name='user-profile-no-slash'),
    path('profile/avatar', views.update_avatar, name='update-avatar-no-slash'),
    # Other endpoints
    path('change-password/', views.change_password, name='change-password'),
    path('change-password', views.change_password, name='change-password-no-slash'),
    path('account/', views.delete_account, name='delete-account'),
]
