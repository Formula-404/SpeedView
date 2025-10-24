# apps/driver/tests.py
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from . import views
from .models import Driver, DriverEntry, DriverTeam
from .forms import DriverForm
from apps.team.models import Team



def json_dumps(obj):
    import json as _json
    return _json.dumps(obj)


class DriverBaseTest(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(username="u1", password="pw12345")
        self.client.login(username="u1", password="pw12345")
        self.d1 = Driver.objects.create(
            driver_number=1, full_name="Max Verstappen", broadcast_name="M VERSTAPPEN"
        )


class TestHelpersAndModels(DriverBaseTest):
    def test_is_admin_false_when_no_profile(self):
        req = SimpleNamespace(user=self.user)
        self.assertFalse(views.is_admin(req))

    def test_serialize_driver_and_session_keys(self):
        data = views.serialize_driver(self.d1)
        self.assertEqual(data["driver_number"], 1)
        self.assertIn("detail_url", data)
        self.assertEqual(self.d1.session_keys, [])

    def test_model_str_and_absolute_url_and_entry_str(self):
        self.assertIn("1 -", str(self.d1))
        self.assertEqual(
            self.d1.get_absolute_url(),
            reverse("driver:driver_detail", kwargs={"driver_number": 1}),
        )
        de = DriverEntry(driver=self.d1, session_key=777, meeting=None)
        self.assertEqual(str(de), "Entry #1 @ session 777")

    def test_driverteam_str_without_saving(self):
        team = Team.objects.create(team_name="Dummy Team")
        link = DriverTeam(driver=self.d1, team=team)
        self.assertEqual(str(link), f"{self.d1.driver_number} ↔ {team}")


class TestForms(DriverBaseTest):
    def test_form_valid_and_update_same_number_allowed(self):
        form = DriverForm(data={"driver_number": 2, "full_name": "Lewis Hamilton"})
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.driver_number, 2)

        # Update pakai nomor sama -> valid
        form2 = DriverForm(data={"driver_number": 2}, instance=obj)
        self.assertTrue(form2.is_valid())

    def test_form_duplicate_number_rejected(self):
        form = DriverForm(data={"driver_number": 1})
        self.assertFalse(form.is_valid())
        self.assertIn(
            "A driver with this number already exists.",
            form.errors["driver_number"],
        )


class TestPages(DriverBaseTest):
    def test_driver_list_page_context(self):
        res = self.client.get(reverse("driver:driver_list"))
        self.assertEqual(res.status_code, 200)
        self.assertIn("drivers", res.context)
        self.assertFalse(res.context["is_admin"])

    def test_driver_list_page_context_admin_true(self):
        with patch("apps.driver.views.is_admin", return_value=True):
            res = self.client.get(reverse("driver:driver_list"))
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.context["is_admin"])

    def test_driver_detail_page(self):
        res = self.client.get(
            reverse("driver:driver_detail", kwargs={"driver_number": 1})
        )
        self.assertEqual(res.status_code, 200)

    def test_add_driver_page_redirect_when_not_admin(self):
        res = self.client.get(reverse("driver:add_page"))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse("driver:driver_list"))

    def test_add_driver_page_ok_when_admin(self):
        with patch("apps.driver.views.is_admin", return_value=True):
            res = self.client.get(reverse("driver:add_page"))
            self.assertEqual(res.status_code, 200)

    def test_edit_driver_page_redirect_when_not_admin(self):
        res = self.client.get(
            reverse("driver:edit_page", kwargs={"driver_number": 1})
        )
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res.url, reverse("driver:driver_detail", kwargs={"driver_number": 1})
        )

    def test_edit_driver_page_ok_when_admin(self):
        with patch("apps.driver.views.is_admin", return_value=True):
            res = self.client.get(
                reverse("driver:edit_page", kwargs={"driver_number": 1})
            )
            self.assertEqual(res.status_code, 200)

    def test_delete_driver_page_redirect_when_not_admin(self):
        res = self.client.get(
            reverse("driver:delete_page", kwargs={"driver_number": 1})
        )
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res.url, reverse("driver:driver_detail", kwargs={"driver_number": 1})
        )

    def test_delete_driver_page_get_and_post_when_admin(self):
        with patch("apps.driver.views.is_admin", return_value=True):
            # GET konfirmasi
            res_get = self.client.get(
                reverse("driver:delete_page", kwargs={"driver_number": 1})
            )
            self.assertEqual(res_get.status_code, 200)
            # POST hapus
            res_post = self.client.post(
                reverse("driver:delete_page", kwargs={"driver_number": 1})
            )
            self.assertEqual(res_post.status_code, 302)
            self.assertEqual(res_post.url, reverse("driver:driver_list"))
            self.assertFalse(Driver.objects.filter(pk=1).exists())


class TestAPI(DriverBaseTest):
    def test_api_list_and_detail(self):
        res = self.client.get(reverse("driver:api_list"))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ok"])
        self.assertEqual(res.json()["count"], 1)

        res2 = self.client.get(
            reverse("driver:api_detail", kwargs={"driver_number": 1})
        )
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["data"]["driver_number"], 1)

    def test_api_create_unauth_and_forbidden(self):
        # 401
        self.client.logout()
        res = self.client.post(
            reverse("driver:api_create"),
            data={"driver_number": 9},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(res.status_code, 401)

        # 403
        self.client.login(username="u1", password="pw12345")
        res2 = self.client.post(
            reverse("driver:api_create"),
            data={"driver_number": 9},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(res2.status_code, 403)

    def test_api_create_invalid_json_success_redirect_422_and_integrity_error_branch(self):
        self.client.login(username="u1", password="pw12345")
        with patch("apps.driver.views.is_admin", return_value=True):
            url = reverse("driver:api_create")

            # Invalid JSON -> 400 (parse_json returns None)
            bad = self.client.post(url, data="}{", content_type="application/json")
            self.assertEqual(bad.status_code, 400)

            # Success (valid JSON) tapi non-AJAX & Accept bukan JSON -> redirect
            ok_redirect = self.client.post(
                url, data=json_dumps({"driver_number": 33, "full_name": "New Guy"}),
                content_type="application/json"
            )
            self.assertEqual(ok_redirect.status_code, 302)
            self.assertEqual(ok_redirect.url, reverse("driver:driver_list"))
            self.assertTrue(Driver.objects.filter(pk=33).exists())

            # 422 JSON (invalid form)
            got_422 = self.client.post(
                url,
                data=json_dumps({"full_name": "No Number"}),
                content_type="application/json",
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                HTTP_ACCEPT="application/json",
            )
            self.assertEqual(got_422.status_code, 422)
            self.assertIn("field_errors", got_422.json())

            # IntegrityError branch: form valid tapi save melempar IntegrityError
            with patch.object(DriverForm, "save", side_effect=views.IntegrityError):
                resp_ie = self.client.post(
                    url,
                    data=json_dumps({"driver_number": 44, "full_name": "Lewis"}),
                    content_type="application/json",
                    HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                    HTTP_ACCEPT="application/json",
                )
                self.assertEqual(resp_ie.status_code, 422)
                self.assertFalse(resp_ie.json()["ok"])

    def test_api_update_all_paths_and_integrity_error_branch(self):
        target = Driver.objects.create(driver_number=3, full_name="Update Me")

        # 401
        self.client.logout()
        res401 = self.client.post(
            reverse("driver:api_update", kwargs={"driver_number": 3}), data={}
        )
        self.assertEqual(res401.status_code, 401)

        # 403
        self.client.login(username="u1", password="pw12345")
        res403 = self.client.post(
            reverse("driver:api_update", kwargs={"driver_number": 3}), data={}
        )
        self.assertEqual(res403.status_code, 403)

        with patch("apps.driver.views.is_admin", return_value=True):
            url = reverse("driver:api_update", kwargs={"driver_number": 3})

            # Invalid JSON -> 400
            res400 = self.client.post(url, data="}{", content_type="application/json")
            self.assertEqual(res400.status_code, 400)

            # OK JSON (Accept JSON supaya tidak redirect)
            res_ok = self.client.post(
                url,
                data=json_dumps({"driver_number": 3, "full_name": "Updated"}),
                content_type="application/json",
                HTTP_ACCEPT="application/json",
            )
            self.assertEqual(res_ok.status_code, 200)
            self.assertEqual(res_ok.json()["data"]["full_name"], "Updated")

            # Redirect branch (non-AJAX & Accept bukan JSON)
            res_redirect = self.client.post(url, data={"driver_number": 3, "full_name": "Updated Again"})
            self.assertEqual(res_redirect.status_code, 302)
            self.assertEqual(res_redirect.url, reverse("driver:driver_list"))

            # 422 (dup number)
            res_422 = self.client.post(
                url,
                data=json_dumps({"driver_number": 1}),
                content_type="application/json",
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                HTTP_ACCEPT="application/json",
            )
            self.assertEqual(res_422.status_code, 422)

            # IntegrityError branch
            with patch.object(DriverForm, "save", side_effect=views.IntegrityError):
                res_ie = self.client.post(
                    url,
                    data=json_dumps({"driver_number": 3, "full_name": "X"}),
                    content_type="application/json",
                    HTTP_ACCEPT="application/json",
                )
                self.assertEqual(res_ie.status_code, 422)

    def test_api_delete_paths(self):
        victim = Driver.objects.create(driver_number=88, full_name="Victim")

        # 401
        self.client.logout()
        res401 = self.client.post(
            reverse("driver:api_delete", kwargs={"driver_number": victim.pk})
        )
        self.assertEqual(res401.status_code, 401)

        # 403
        self.client.login(username="u1", password="pw12345")
        res403 = self.client.post(
            reverse("driver:api_delete", kwargs={"driver_number": victim.pk})
        )
        self.assertEqual(res403.status_code, 403)

        # 200 OK (admin)
        with patch("apps.driver.views.is_admin", return_value=True):
            res_ok = self.client.post(
                reverse("driver:api_delete", kwargs={"driver_number": victim.pk})
            )
            self.assertEqual(res_ok.status_code, 200)
            self.assertTrue(res_ok.json()["ok"])
            self.assertFalse(Driver.objects.filter(pk=victim.pk).exists())
