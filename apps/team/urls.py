from django.urls import path
from . import views

app_name = "team"

urlpatterns = [
    # API
    path("api/", views.api_team_list, name="api_list"),
    path("api/create/", views.api_team_create, name="api_create"),
    path("api/<str:team_name>/", views.api_team_detail, name="api_detail"),
    path("api/<str:team_name>/update/", views.api_team_update, name="api_update"),
    path("api/<str:team_name>/delete/", views.api_team_delete, name="api_delete"),

    # Page
    path("", views.team_list_page, name="list_page"),
    path("add/", views.add_team_page, name="add_page"),
    path("<str:team_name>/", views.team_detail_page, name="detail_page"),
    path("<str:team_name>/edit/", views.edit_team_page, name="edit_page"),

    # Mobile API
    path('api/mobile/', views.api_mobile_team_list, name='api_mobile_comparison_list'),
    path("api/mobile/create/", views.api_mobile_team_create, name="api_mobile_create"),
    path("api/mobile/<uuid:pk>/edit/", views.api_mobile_team_update, name="api_mobile_update"),
    path("api/mobile/<uuid:pk>/delete/", views.api_mobile_team_delete, name="api_mobile_delete"),
]