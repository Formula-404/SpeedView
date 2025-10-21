from django.urls import path
from . import views

app_name = "user"

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('beritauatminrajamauregister/', views.register_admin_view, name='register_admin'),
    path('profile/settings/', views.profile_settings_view, name='profile_settings'),
]
