from django.urls import path
from . import views

app_name = "pit"

urlpatterns = [
    # API
    path("api/", views.api_pit_list, name="api_pit_list"),
    path("api/<int:pit_id>/", views.api_pit_detail, name="api_pit_detail"),

    # Page
    path("", views.pit_list_page, name="pit_list_page"),
    path("<int:pit_id>/", views.pit_detail_page, name="pit_detail_page"),
]
