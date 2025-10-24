from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.session.models import Session
from apps.meeting.models import Meeting


class SessionModelTest(TestCase):
    def setUp(self):
        self.meeting = Meeting.objects.create(meeting_key=1, meeting_name='Test GP', year=2024)
        self.session = Session.objects.create(
            session_key=1, meeting_key=1, name='Race', start_time=timezone.now()
        )

    def test_session_all_features(self):
        self.assertEqual(self.session.session_key, 1)
        self.assertEqual(self.session.meeting_key, 1)
        self.assertEqual(self.session.name, 'Race')
        self.assertIn('1 - RACE', str(self.session))

        self.session.name = 'Qualifying'
        self.session.save()
        self.assertEqual(self.session.name, 'Qualifying')

        session_key = self.session.session_key
        self.session.delete()
        self.assertFalse(Session.objects.filter(session_key=session_key).exists())

    def test_session_str_no_name(self):
        session = Session.objects.create(session_key=2, meeting_key=1)
        self.assertEqual(str(session), '2')


class SessionViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.meeting = Meeting.objects.create(
            meeting_key=1, meeting_name='Test GP', circuit_short_name='Test',
            country_name='Test Country', year=2024, date_start=timezone.now()
        )
        self.session = Session.objects.create(
            session_key=1, meeting_key=1, name='Race', start_time=timezone.now()
        )

    def test_session_list_page(self):
        response = self.client.get(reverse('session:list_page'))
        self.assertEqual(response.status_code, 200)

    def test_api_session_list(self):
        response = self.client.get(reverse('session:api_list'))
        self.assertEqual(response.status_code, 200)

    def test_api_session_list_with_query(self):
        response = self.client.get(reverse('session:api_list'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)

    def test_api_session_list_with_page(self):
        response = self.client.get(reverse('session:api_list'), {'page': 1})
        self.assertEqual(response.status_code, 200)
