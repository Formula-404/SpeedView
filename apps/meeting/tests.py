from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.meeting.models import Meeting


class MeetingModelTest(TestCase):
    def setUp(self):
        self.meeting = Meeting.objects.create(
            meeting_key=1, meeting_name='Bahrain Grand Prix', circuit_short_name='Bahrain',
            country_name='Bahrain', year=2024, date_start=timezone.now()
        )

    def test_meeting_all_features(self):
        self.assertEqual(self.meeting.meeting_key, 1)
        self.assertEqual(self.meeting.meeting_name, 'Bahrain Grand Prix')
        self.assertEqual(self.meeting.circuit_short_name, 'Bahrain')
        self.assertEqual(self.meeting.country_name, 'Bahrain')
        self.assertEqual(self.meeting.year, 2024)
        self.assertEqual(str(self.meeting), 'Bahrain Grand Prix (2024)')

        self.meeting.year = 2025
        self.meeting.save()
        self.assertEqual(self.meeting.year, 2025)

        meeting_key = self.meeting.meeting_key
        self.meeting.delete()
        self.assertFalse(Meeting.objects.filter(meeting_key=meeting_key).exists())


class MeetingViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.meeting = Meeting.objects.create(
            meeting_key=1, meeting_name='Bahrain Grand Prix', circuit_short_name='Bahrain',
            country_name='Bahrain', year=2024, date_start=timezone.now()
        )

    def test_meeting_list_page(self):
        response = self.client.get(reverse('meeting:list_page'))
        self.assertEqual(response.status_code, 200)

    def test_api_meeting_list(self):
        response = self.client.get(reverse('meeting:api_list'))
        self.assertEqual(response.status_code, 200)

    def test_api_meeting_list_with_query(self):
        response = self.client.get(reverse('meeting:api_list'), {'q': 'Bahrain'})
        self.assertEqual(response.status_code, 200)

    def test_api_meeting_list_with_page(self):
        response = self.client.get(reverse('meeting:api_list'), {'page': 1})
        self.assertEqual(response.status_code, 200)
