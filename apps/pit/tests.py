from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import TestCase, Client
from django.urls import reverse

from . import views 


class PitViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

    # ---------- helper tests ----------
    def test_fmt_none_and_invalid(self):
        self.assertIsNone(views._fmt(None))
        self.assertEqual(views._fmt("not-a-date"), "not-a-date")

    def test_fmt_valid_iso(self):
        s = "2024-05-01T12:34:56"
        self.assertEqual(views._fmt(s), "01 May, 12:34")

    # ---------- page tests ----------
    def test_pit_list_page_ok(self):
        url = reverse("pit:pit_list_page")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    # ---------- API tests ----------
    @patch("apps.pit.views.requests.get")
    def test_api_pit_list_success_without_params(self, mock_get):
        payload = [
            {"date": "2024-05-01T12:34:56", "driver_number": 1},
            {"date": "bad-date", "driver_number": 2},
            {"date": None, "driver_number": 3},
        ]
        mock_resp = Mock()
        mock_resp.json.return_value = payload
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        url = reverse("pit:api_pit_list")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        js = resp.json()
        self.assertTrue(js["ok"])
        self.assertEqual(js["count"], 3)

        # cek formatting date_str untuk tiap baris
        self.assertEqual(js["data"][0]["date_str"], "01 May, 12:34") 
        self.assertEqual(js["data"][1]["date_str"], "bad-date")      
        self.assertIsNone(js["data"][2]["date_str"])

        # cek pemanggilan requests.get (tanpa params)
        mock_get.assert_called_once_with(
            f"{views.OPENF1_API_BASE_URL}/pit",
            params={},
            timeout=20,
        )

    @patch("apps.pit.views.requests.get")
    def test_api_pit_list_success_with_params(self, mock_get):
        mock_resp = Mock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        url = (
            reverse("pit:api_pit_list")
            + "?session_key=11&driver_number=44&lap_number=7&meeting_key=2024"
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])

        # pastikan params diteruskan persis
        mock_get.assert_called_once_with(
            f"{views.OPENF1_API_BASE_URL}/pit",
            params={"session_key": "11", "driver_number": "44", "lap_number": "7", "meeting_key": "2024"},
            timeout=20,
        )

    @patch("apps.pit.views.requests.get")
    def test_api_pit_list_request_exception(self, mock_get):
        import requests

        mock_get.side_effect = requests.RequestException("boom")
        resp = self.client.get(reverse("pit:api_pit_list"))
        self.assertEqual(resp.status_code, 502)
        js = resp.json()
        self.assertFalse(js["ok"])
        self.assertIn("boom", js["error"])
