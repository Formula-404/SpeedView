from django.urls import path
from .views import CircuitList, CircuitDetail, CircuitCreate, CircuitUpdate, CircuitDelete

app_name = "circuit"

urlpatterns = [
    path('', CircuitList.as_view(), name='circuit_list'),
    path('<int:pk>/', CircuitDetail.as_view(), name='circuit_detail'),
    path('new/', CircuitCreate.as_view(), name='circuit_create'),
    path('<int:pk>/edit/', CircuitUpdate.as_view(), name='circuit_update'),
    path('<int:pk>/delete/', CircuitDelete.as_view(), name='circuit_delete'),
]
