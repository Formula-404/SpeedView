from django.urls import path
from . import views

app_name = "meeting"

urlpatterns = [
    path("", views.meeting_list_page, name="list_page"),
    path("api/", views.api_meeting_list, name="api_list"),
]
