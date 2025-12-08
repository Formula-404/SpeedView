from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.driver.models import Driver
from apps.meeting.models import Meeting
from apps.session.models import Session
from apps.weather.models import Weather


class MainViewsTest(TestCase):
    def test_api_recent_meetings_returns_latest_local_rows(self):
        base = timezone.now()
        for idx in range(5):
            Meeting.objects.create(
                meeting_key=idx + 1,
                meeting_name=f"Meeting {idx + 1}",
                date_start=base - timedelta(days=idx),
            )

        resp = self.client.get(reverse("main:api_recent_meetings"))
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["data"]), 4)
        keys = [row["meeting_key"] for row in payload["data"]]
        # Most recent meetings should appear first.
        self.assertEqual(keys, [5, 4, 3, 2])

    def test_api_dashboard_data_uses_database_models(self):
        meeting = Meeting.objects.create(
            meeting_key=99,
            meeting_name="Local GP",
            circuit_short_name="LOC",
            country_name="Nowhere",
            year=2024,
            date_start=timezone.now(),
        )
        Session.objects.create(session_key=1001, meeting_key=meeting.meeting_key, name="Practice", start_time=timezone.now())
        Session.objects.create(session_key=1002, meeting_key=meeting.meeting_key, name="Race", start_time=timezone.now())
        Weather.objects.create(meeting=meeting, date=timezone.now(), air_temperature=30, track_temperature=40)
        Driver.objects.create(driver_number=1, full_name="Test Driver")

        resp = self.client.get(
            reverse("main:api_dashboard_data"),
            {"meeting_key": meeting.meeting_key},
        )

        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["ok"])
        data = payload["data"]
        self.assertEqual(data["meeting"]["meeting_key"], meeting.meeting_key)
        self.assertEqual(len(data["sessions"]), 2)
        self.assertEqual(data["sessions"][-1]["session_key"], 1002)
        self.assertEqual(len(data["weather"]), 1)
        self.assertEqual(data["weather"][0]["air_temperature"], 30)
        self.assertEqual(len(data["drivers"]), 1)
