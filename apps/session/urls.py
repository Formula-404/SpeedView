from django.urls import path
from . import views

app_name = "session"

urlpatterns = [
    path('', views.session_list, name='session_list'),
    path('<int:meeting_key>/import/', views.add_sessions, name='add_sessions'),
]
