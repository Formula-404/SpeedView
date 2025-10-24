from django.urls import path
from . import views

app_name = "circuit"

urlpatterns = [
    path("api/", views.api_circuit_list, name="api_list"),
    path("api/create/", views.api_circuit_create, name="api_create"),
    path("api/<int:pk>/update/", views.api_circuit_update, name="api_update"),
    path("api/<int:pk>/delete/", views.api_circuit_delete, name="api_delete"),
    path("", views.circuit_list_page, name="list_page"),
    path("add/", views.add_circuit_page, name="add_page"),
    path("<int:pk>/", views.circuit_detail_page, name="detail_page"),
    path("<int:pk>/edit/", views.edit_circuit_page, name="edit_page")
]
