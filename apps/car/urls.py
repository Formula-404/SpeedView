from django.urls import path

from . import views

app_name = "car"

urlpatterns = [
    path("", views.show_main, name="show_main"),
    path("manual/", views.manual_list, name="manual_list"),
    path("manual/json/", views.manual_json, name="manual_json"),
    path("all/", views.all_cars_dashboard, name="list_page"),
    path("api/grouped/", views.api_grouped_car_data, name="api_grouped"),
    path("api/refresh/", views.api_refresh_car_data, name="api_refresh"),
    path("add/", views.add_car, name="add_car"),
    path("<int:id>/", views.show_car, name="show_car"),
    path("<int:id>/edit/", views.edit_car, name="edit_car"),
    path("<int:id>/delete/", views.delete_car, name="delete_car"),
    path("telemetry/create-ajax/", views.add_car_entry_ajax, name="add_car_entry_ajax"),
    path(
        "telemetry/<int:car_id>/update-ajax/",
        views.update_car_entry_ajax,
        name="update_car_entry_ajax",
    ),
    path(
        "telemetry/<int:car_id>/delete-ajax/",
        views.delete_car_entry_ajax,
        name="delete_car_entry_ajax",
    ),
    path("xml/", views.show_xml, name="show_xml"),
    path("json/", views.show_json, name="show_json"),
    path("xml/<int:car_id>/", views.show_xml_by_id, name="show_xml_by_id"),
    path("json/<int:car_id>/", views.show_json_by_id, name="show_json_by_id"),
]
