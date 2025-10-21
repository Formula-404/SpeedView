from django.urls import path

from apps.car.views import (
    add_car,
    add_car_entry_ajax,
    delete_car,
    edit_car,
    show_car,
    show_json,
    show_json_by_id,
    show_main,
    show_xml,
    show_xml_by_id,
)
app_name = "car"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("add/", add_car, name="add_car"),
    path("<int:id>/", show_car, name="show_car"),
    path("<int:id>/edit/", edit_car, name="edit_car"),
    path("<int:id>/delete/", delete_car, name="delete_car"),
    path("telemetry/create-ajax/", add_car_entry_ajax, name="add_car_entry_ajax"),
    path("xml/", show_xml, name="show_xml"),
    path("json/", show_json, name="show_json"),
    path("xml/<int:car_id>/", show_xml_by_id, name="show_xml_by_id"),
    path("json/<int:car_id>/", show_json_by_id, name="show_json_by_id"),
]
