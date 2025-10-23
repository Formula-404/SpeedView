# apps/laps/urls.py
from django.urls import path
from . import views

app_name = "laps"

urlpatterns = [
    path("", views.laps_list_page, name="laps_list_page"),
    path("api/", views.api_laps_list, name="api_laps_list"),
    path("<int:driver_number>/", views.lap_detail_page, name="lap_detail_page"),
]

