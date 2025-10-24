from django.urls import path
from . import views

app_name = "comparison"

urlpatterns = [
    # API
    path("api/list/", views.api_comparison_list, name="api_list"),
    path("api/create/", views.api_comparison_create, name="api_create"),
    path("api/<uuid:pk>/", views.api_comparison_detail, name="api_detail"),
    path("api/<uuid:pk>/delete/", views.api_comparison_delete, name="api_delete"),

    # Page
    path("", views.list_page, name="list_page"),
    path("create/", views.create_page, name="create_page"),
    path("<uuid:pk>/", views.detail_page, name="detail_page"),
]
