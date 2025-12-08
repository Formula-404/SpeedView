# apps/driver/urls.py

from django.urls import path
from . import views

app_name = "driver"

urlpatterns = [
    # API (web + umum)
    path("api/", views.api_driver_list, name="api_list"),
    path("api/create/", views.api_driver_create, name="api_create"),
    path("api/<int:driver_number>/", views.api_driver_detail, name="api_detail"),
    path("api/<int:driver_number>/update/", views.api_driver_update, name="api_update"),
    path("api/<int:driver_number>/delete/", views.api_driver_delete, name="api_delete"),
    path(
        "api/driver-entry-availability",
        views.api_driver_entry_availability_by_session,
        name="api_driver_entry_availability_by_session",
    ),

    # Page
    path("", views.driver_list_page, name="driver_list"),
    path("add/", views.add_driver_page, name="add_page"),
    path("<int:driver_number>/", views.driver_detail_page, name="driver_detail"),
    path("<int:driver_number>/edit/", views.edit_driver_page, name="edit_page"),
    path("<int:driver_number>/delete/confirm/", views.delete_driver_page, name="delete_page"),

    # ========= Mobile API (khusus Flutter) =========
    path("api/mobile/", views.api_mobile_driver_list, name="api_mobile_list"),
    path("api/mobile/create/", views.api_mobile_driver_create, name="api_mobile_create"),
    path("api/mobile/<int:driver_number>/update/", views.api_mobile_driver_update, name="api_mobile_update"),
    path("api/mobile/<int:driver_number>/delete/", views.api_mobile_driver_delete, name="api_mobile_delete"),
]
