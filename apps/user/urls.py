from django.urls import path
from . import views

app_name = "user"

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('beritauatminrajamauregister/', views.register_admin_view, name='register_admin'),
    path('profile/settings/', views.profile_settings_view, name='profile_settings'),
    path('login-flutter/', views.login_flutter, name='login_flutter'),
    path('register-flutter/', views.register_flutter, name='register_flutter'),
    path('logout-flutter/', views.logout_flutter, name='logout_flutter'),
    path('profile-flutter/', views.get_user_profile, name='get_user_profile'),
    path('edit-profile-flutter/', views.edit_profile_flutter, name='edit_profile_flutter'),
]
