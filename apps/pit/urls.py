# apps/pit/urls.py
from django.urls import path
from . import views

app_name = "pit"

urlpatterns = [
    path("", views.pit_list_page, name="pit_list_page"),
    path("api/", views.api_pit_list, name="api_pit_list"),
    #path("<int:driver_number>/", views.pit_detail_page, name="pit_detail_page"),
]
