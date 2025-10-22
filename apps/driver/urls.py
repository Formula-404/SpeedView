from django.urls import path
from . import views

app_name = 'driver'

urlpatterns = [
    path('',                         views.DriverList.as_view(),   name='driver_list'),
    path('add/',                     views.DriverCreate.as_view(), name='driver_add'),
    path('<int:pk>/',                views.DriverDetail.as_view(), name='driver_detail'),
    path('<int:pk>/edit/',           views.DriverUpdate.as_view(), name='driver_edit'),
    path('<int:pk>/delete/',         views.DriverDelete.as_view(), name='driver_delete'),

    # XML / JSON
    path('xml/',                     views.show_xml,        name='show_xml'),
    path('json/',                    views.show_json,       name='show_json'),
    path('xml/<int:driver_number>/', views.show_xml_by_id,  name='show_xml_by_id'),
    path('json/<int:driver_number>/',views.show_json_by_id, name='show_json_by_id'),
]
