from django.urls import path
from . import views

app_name = "weather"

urlpatterns = [
    path('', views.weather_list_page, name='list_page'),
    path('api/', views.api_weather_list, name='api_list'),
]
