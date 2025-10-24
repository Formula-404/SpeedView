from types import SimpleNamespace
from unittest.mock import patch, Mock

import requests
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse

from . import views


class LapsViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.rf = RequestFactory()

    # ===== helpers =====
    def test_fmt_none_invalid_valid(self):
        self.assertIsNone(views._fmt(None))                      # None -> None
        self.assertEqual(views._fmt("not-a-date"), "not-a-date") # invalid -> sama
        self.assertEqual(views._fmt("2024-05-01T12:34:56"), "01 May, 12:34")  # valid ISO

    @patch("apps.laps.views.requests.get")
    def test_fetch_laps_default_and_formatting(self, mock_get):
        payload = [
            {"date_start": "2024-05-01T12:34:56", "lap_number": 1},
            {"date_start": "bad", "lap_number": 2},
            {"date_start": None, "lap_number": 3},
        ]
        resp = Mock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = payload
        mock_get.return_value = resp

        data = views._fetch_laps({})  # empty -> fallback meeting_key=latest
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["date_start_str"], "01 May, 12:34")
        self.assertEqual(data[1]["date_start_str"], "bad")
        self.assertIsNone(data[2]["date_start_str"])

        mock_get.assert_called_once_with(
            f"{views.OPENF1_API_BASE_URL}/laps",
            params={"meeting_key": "latest"},
            timeout=20,
        )

    @patch("apps.laps.views.requests.get")
    def test_fetch_laps_filters_out_empty_values(self, mock_get):
        payload = []
        resp = Mock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = payload
        mock_get.return_value = resp

        params = {"session_key": "", "driver_number": None, "meeting_key": "123"}
        _ = views._fetch_laps(params)
        mock_get.assert_called_once_with(
            f"{views.OPENF1_API_BASE_URL}/laps",
            params={"meeting_key": "123"},
            timeout=20,
        )

    # ===== pages =====
    def test_laps_list_page_ok(self):
        url = reverse("laps:laps_list_page")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

    def test_lap_detail_page_direct_call(self):
        # tidak ada route; panggil langsung
        req = self.rf.get("/laps/44/")
        r = views.lap_detail_page(req, 44)
        self.assertEqual(r.status_code, 200)

    # ===== API =====
    @patch("apps.laps.views.requests.get")
    def test_api_laps_list_success_no_params_uses_fallback(self, mock_get):
        payload = [{"date_start": "2024-05-01T12:34:56"}]
        resp = Mock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = payload
        mock_get.return_value = resp

        url = reverse("laps:api_laps_list")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        js = r.json()
        self.assertTrue(js["ok"])
        self.assertEqual(js["count"], 1)
        self.assertEqual(js["data"][0]["date_start_str"], "01 May, 12:34")

        mock_get.assert_called_once_with(
            f"{views.OPENF1_API_BASE_URL}/laps",
            params={"meeting_key": "latest"},
            timeout=20,
        )

    @patch("apps.laps.views.requests.get")
    def test_api_laps_list_success_with_params(self, mock_get):
        resp = Mock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = []
        mock_get.return_value = resp

        url = reverse("laps:api_laps_list") + "?session_key=5&driver_number=22&lap_number=7&meeting_key=2024"
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["ok"])

        mock_get.assert_called_once_with(
            f"{views.OPENF1_API_BASE_URL}/laps",
            params={"session_key": "5", "driver_number": "22", "lap_number": "7", "meeting_key": "2024"},
            timeout=20,
        )

    def _make_http_error(self, code=400, reason="Bad Request"):
        e = requests.HTTPError(f"{code} {reason}")
        e.response = SimpleNamespace(status_code=code, reason=reason)
        return e

    @patch("apps.laps.views._fetch_laps")
    def test_api_laps_list_http_error_no_params_has_hint(self, mock_fetch):
        mock_fetch.side_effect = self._make_http_error(400, "Bad Request")
        url = reverse("laps:api_laps_list")  # no params
        r = self.client.get(url)
        self.assertEqual(r.status_code, 502)
        msg = r.json()["error"]
        self.assertIn("400 Client Error: Bad Request", msg)
        self.assertIn("minimal satu filter", msg)  # ada saran

    @patch("apps.laps.views._fetch_laps")
    def test_api_laps_list_http_error_with_params_no_hint(self, mock_fetch):
        mock_fetch.side_effect = self._make_http_error(404, "Not Found")
        url = reverse("laps:api_laps_list") + "?session_key=5"
        r = self.client.get(url)
        self.assertEqual(r.status_code, 502)
        msg = r.json()["error"]
        self.assertIn("404 Client Error: Not Found", msg)
        # tidak ada saran tambahan
        self.assertNotIn("minimal satu filter", msg)

    @patch("apps.laps.views._fetch_laps")
    def test_api_laps_list_request_exception(self, mock_fetch):
        mock_fetch.side_effect = requests.RequestException("boom")
        r = self.client.get(reverse("laps:api_laps_list"))
        self.assertEqual(r.status_code, 502)
        self.assertIn("boom", r.json()["error"])
