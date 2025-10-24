from django.urls import path
from . import views

app_name = "session"

urlpatterns = [
    path("", views.session_list_page, name="list_page"),
    path("api/", views.api_session_list, name="api_list"),
]
