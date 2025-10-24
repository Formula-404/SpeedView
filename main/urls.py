from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    #path('', show_main, name='show_main'),
    path("", views.main_dashboard_page, name="show_main"),
    path("api/recent-meetings/", views.api_recent_meetings, name="api_recent_meetings"),    
    path("api/dashboard-data/", views.api_dashboard_data, name="api_dashboard_data"),
]