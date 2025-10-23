from django.urls import path
from . import views

app_name = "pit"

urlpatterns = [
    path("", views.pit_list_page, name="pit_list_page"),
    path("api/", views.api_pit_list, name="api_pit_list"),
]
