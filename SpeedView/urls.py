"""
URL configuration for SpeedView project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include

urlpatterns = [
    path('', include('main.urls')),
    path('', include('apps.user.urls')),
    path('driver/', include('apps.driver.urls')),
    path('circuit/', include('apps.circuit.urls')),
    path('meeting/', include('apps.meeting.urls')),
    path('session/', include('apps.session.urls')),
    path('weather/', include('apps.weather.urls')),
    path('team/', include('apps.team.urls')),
    path('car/', include('apps.car.urls')),
    path('laps/', include('apps.laps.urls')),
    path('pit/', include('apps.pit.urls')),
    path('comparison/', include('apps.comparison.urls')),
]
