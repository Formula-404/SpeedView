from django.urls import path
from . import views

app_name = "laps"

urlpatterns = [
    # API
    path("api/", views.api_laps_list, name="api_laps_list"),
    path("api/<int:lap_number>/", views.api_lap_detail, name="api_lap_detail"),

    # Page
    path("", views.laps_list_page, name="laps_list_page"),
    path("<int:lap_number>/", views.lap_detail_page, name="lap_detail_page"),
]
