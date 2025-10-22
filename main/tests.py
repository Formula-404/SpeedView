from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError, transaction
import json

# Import dari apps baru (bukan dari main)
from apps.driver.models import Driver
from apps.laps.models import Laps
from apps.pit.models import Pit


class MainSmokeTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_root_url_exists_and_uses_template(self):
        """
        Root ('/') harus 200 dan menggunakan template landing: main/home.html.
        """
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "main/home.html")

    def test_nonexistent_page_returns_404(self):
        resp = self.client.get("/burhan_always_exists/")
        self.assertEqual(resp.status_code, 404)


class DriverModelAndAPITest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_driver_creation_minimal_and_defaults(self):
        """
        Buat Driver minimal (hanya PK) dan cek default/kosongan aman.
        """
        d = Driver.objects.create(driver_number=44)
        self.assertEqual(d.driver_number, 44)
        # field opsional mestinya kosong/None sesuai definisi model
        self.assertEqual(d.country_code, "")
        self.assertEqual(d.team_name, "")
        self.assertIsNone(d.meeting_key)
        self.assertIsNone(d.session_key)
        # __str__ harus menyertakan nomor driver
        self.assertIn("44", str(d))

    def test_driver_list_and_detail_pages_render(self):
        """
        Halaman list & detail driver harus bisa diakses publik.
        """
        d = Driver.objects.create(driver_number=16, full_name="Charles Leclerc")

        # /driver/  → template driver/driver_list.html
        resp_list = self.client.get(reverse("driver:driver_list"))
        self.assertEqual(resp_list.status_code, 200)
        self.assertTemplateUsed(resp_list, "driver/driver_list.html")

        # /driver/<pk>/ → template driver/driver_detail.html
        resp_detail = self.client.get(reverse("driver:driver_detail", kwargs={"pk": d.pk}))
        self.assertEqual(resp_detail.status_code, 200)
        self.assertTemplateUsed(resp_detail, "driver/driver_detail.html")
        self.assertContains(resp_detail, "Charles Leclerc")

    def test_json_endpoint_lists_drivers(self):
        Driver.objects.create(driver_number=1, full_name="Max Verstappen")
        Driver.objects.create(driver_number=44, full_name="Lewis Hamilton")

        resp = self.client.get(reverse("driver:show_json"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        payload = json.loads(resp.content.decode())
        # dua objek harus ter-serialize
        self.assertEqual(len(payload), 2)
        # pastikan salah satu punya pk=44
        pks = {int(obj["pk"]) for obj in payload}
        self.assertIn(44, pks)

    def test_xml_endpoint_lists_drivers(self):
        Driver.objects.create(driver_number=16, full_name="Charles Leclerc")
        resp = self.client.get(reverse("driver:show_xml"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/xml")
        self.assertTrue(resp.content.startswith(b'<?xml') or b"<django-objects" in resp.content)

    def test_json_by_id_and_xml_by_id(self):
        d = Driver.objects.create(driver_number=63, full_name="George Russell")

        # JSON by id
        r_json = self.client.get(reverse("driver:show_json_by_id", kwargs={"driver_number": d.pk}))
        self.assertEqual(r_json.status_code, 200)
        data = json.loads(r_json.content.decode())
        self.assertEqual(len(data), 1)
        self.assertEqual(int(data[0]["pk"]), 63)

        # XML by id
        r_xml = self.client.get(reverse("driver:show_xml_by_id", kwargs={"driver_number": d.pk}))
        self.assertEqual(r_xml.status_code, 200)
        self.assertEqual(r_xml["Content-Type"], "application/xml")

        # not found
        r_json_404 = self.client.get(reverse("driver:show_json_by_id", kwargs={"driver_number": 999}))
        r_xml_404 = self.client.get(reverse("driver:show_xml_by_id", kwargs={"driver_number": 999}))
        self.assertEqual(r_json_404.status_code, 404)
        self.assertEqual(r_xml_404.status_code, 404)


class ReadOnlyTablesConstraintTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.driver = Driver.objects.create(driver_number=11, full_name="Sergio Perez")

    def test_laps_unique_constraint(self):
        """
        Kombinasi (driver, session_key, lap_number) harus unik.
        """
        Laps.objects.create(
            driver=self.driver,
            meeting_key=2024,
            session_key=1234,
            date_start=timezone.now(),
            lap_number=1,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Laps.objects.create(
                    driver=self.driver,
                    meeting_key=2024,
                    session_key=1234,
                    date_start=timezone.now(),
                    lap_number=1,  # duplikat
                )

    def test_pit_unique_constraint(self):
        """
        Kombinasi (driver, session_key, lap_number) harus unik.
        """
        Pit.objects.create(
            driver=self.driver,
            meeting_key=2024,
            session_key=5678,
            date=timezone.now(),
            lap_number=10,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Pit.objects.create(
                    driver=self.driver,
                    meeting_key=2024,
                    session_key=5678,
                    date=timezone.now(),
                    lap_number=10,  # duplikat
                )
