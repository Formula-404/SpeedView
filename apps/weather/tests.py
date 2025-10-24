from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.weather.models import Weather
from apps.meeting.models import Meeting


class WeatherModelTest(TestCase):
    def setUp(self):
        self.meeting = Meeting.objects.create(
            meeting_key=1, meeting_name='Test GP', circuit_short_name='Test',
            country_name='Test Country', year=2024, date_start=timezone.now()
        )
        self.weather = Weather.objects.create(
            meeting=self.meeting, date=timezone.now(), air_temperature=25.5,
            track_temperature=35.0, pressure=1013.25, wind_speed=5.5,
            wind_direction=180, humidity=60.0, rainfall=False
        )

    def test_weather_all_features(self):
        self.assertEqual(self.weather.meeting, self.meeting)
        self.assertEqual(self.weather.air_temperature, 25.5)
        self.assertEqual(self.weather.track_temperature, 35.0)
        self.assertEqual(self.weather.pressure, 1013.25)
        self.assertEqual(self.weather.wind_speed, 5.5)
        self.assertEqual(self.weather.wind_direction, 180)
        self.assertEqual(self.weather.humidity, 60.0)
        self.assertEqual(self.weather.rainfall, False)
        self.assertIn('Weather at', str(self.weather))

        self.weather.air_temperature = 26.0
        self.weather.save()
        self.assertEqual(self.weather.air_temperature, 26.0)

        weather_id = self.weather.id
        self.weather.delete()
        self.assertFalse(Weather.objects.filter(id=weather_id).exists())


class WeatherViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.meeting = Meeting.objects.create(
            meeting_key=1, meeting_name='Test GP', circuit_short_name='Test',
            country_name='Test Country', year=2024, date_start=timezone.now()
        )
        self.weather = Weather.objects.create(
            meeting=self.meeting, date=timezone.now(), air_temperature=25.5,
            track_temperature=35.0, pressure=1013.25, wind_speed=5.5,
            wind_direction=180, humidity=60.0, rainfall=False
        )

    def test_api_weather_list(self):
        response = self.client.get(reverse('weather:api_list'))
        self.assertEqual(response.status_code, 200)

    def test_api_weather_list_with_query(self):
        response = self.client.get(reverse('weather:api_list'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
