import json
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.user.models import UserProfile  # <-- real profile
from .models import Team
from . import views as team_views


def make_admin_user(username="adminuser", password="pass12345"):
    User = get_user_model()
    u = User.objects.create_user(username=username, password=password, email=f"{username}@x.test")
    UserProfile.objects.create(id=u, role="admin", theme_preference="dark")
    return u

def make_member_user(username="member", password="pass12345"):
    User = get_user_model()
    u = User.objects.create_user(username=username, password=password, email=f"{username}@x.test")
    UserProfile.objects.create(id=u, role="user", theme_preference="dark")
    return u

def make_json_post(factory: RequestFactory, path: str, user, payload: dict):
    body = json.dumps(payload).encode("utf-8")
    req = factory.post(
        path,
        data=body,
        content_type="application/json",
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        HTTP_ACCEPT="application/json",
    )
    req.user = user
    return req


class TeamModelTests(TestCase):
    def test_str_and_absolute_url(self):
        t = Team.objects.create(
            team_name="Red Bull Racing",
            short_code="RBR",
            team_logo_url="https://example.com/logo.png",
            team_colour="00A19A",
            country="United Kingdom",
        )
        self.assertEqual(str(t), "Red Bull Racing")
        self.assertEqual(
            t.get_absolute_url(),
            reverse("team:detail_page", kwargs={"team_name": "Red Bull Racing"})
        )


class TeamPageViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.team = Team.objects.create(
            team_name="Ferrari",
            short_code="FER",
            team_colour="FF0000",
        )

    def test_list_page_renders(self):
        url = reverse("team:list_page")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_detail_page_renders(self):
        url = reverse("team:detail_page", kwargs={"team_name": self.team.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_add_page_requires_login(self):
        url = reverse("team:add_page")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)

    def test_add_page_requires_admin(self):
        user = make_member_user()
        self.client.login(username=user.username, password="pass12345")
        url = reverse("team:add_page")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)

    def test_add_page_admin_ok(self):
        admin = make_admin_user()
        self.client.login(username=admin.username, password="pass12345")
        url = reverse("team:add_page")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_edit_page_requires_login(self):
        url = reverse("team:edit_page", kwargs={"team_name": self.team.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)

    def test_edit_page_requires_admin(self):
        user = make_member_user()
        self.client.login(username=user.username, password="pass12345")
        url = reverse("team:edit_page", kwargs={"team_name": self.team.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)

    def test_edit_page_admin_ok(self):
        admin = make_admin_user()
        self.client.login(username=admin.username, password="pass12345")
        url = reverse("team:edit_page", kwargs={"team_name": self.team.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)


class TeamApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.admin = make_admin_user()
        self.member = make_member_user()
        self.team = Team.objects.create(
            team_name="McLaren",
            short_code="MCL",
            team_colour="FF8000",
            country="United Kingdom",
        )

    def test_api_list_returns_public_data(self):
        url = reverse("team:api_list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertTrue(payload["ok"])
        self.assertGreaterEqual(payload["count"], 1)
        self.assertEqual(payload["data"][0]["team_name"], "McLaren")

    def test_api_detail_ok(self):
        url = reverse("team:api_detail", kwargs={"team_name": "McLaren"})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["team_name"], "McLaren")
        self.assertIn("detail_url", payload["data"])

    def test_api_detail_404(self):
        url = reverse("team:api_detail", kwargs={"team_name": "Nope"})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 404)

    def test_api_create_requires_auth(self):
        url = reverse("team:api_create")
        res = self.client.post(url, data=json.dumps({}), content_type="application/json", HTTP_X_REQUESTED_WITH="XMLHttpRequest", HTTP_ACCEPT="application/json")
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json()["ok"])

    def test_api_update_requires_auth(self):
        url = reverse("team:api_update", kwargs={"team_name": "McLaren"})
        res = self.client.post(url, data=json.dumps({}), content_type="application/json", HTTP_X_REQUESTED_WITH="XMLHttpRequest", HTTP_ACCEPT="application/json")
        self.assertEqual(res.status_code, 401)

    def test_api_update_requires_admin(self):
        url = reverse("team:api_update", kwargs={"team_name": "McLaren"})
        req = make_json_post(self.factory, url, self.member, {"country": "UK"})
        res = team_views.api_team_update(req, "McLaren")
        self.assertEqual(res.status_code, 403)

    def test_api_delete_requires_auth(self):
        url = reverse("team:api_delete", kwargs={"team_name": "McLaren"})
        res = self.client.post(url, data={}, content_type="application/json", HTTP_X_REQUESTED_WITH="XMLHttpRequest", HTTP_ACCEPT="application/json")
        self.assertEqual(res.status_code, 401)

    def test_api_delete_requires_admin(self):
        url = reverse("team:api_delete", kwargs={"team_name": "McLaren"})
        req = self.factory.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest", HTTP_ACCEPT="application/json")
        req.user = self.member
        res = team_views.api_team_delete(req, "McLaren")
        self.assertEqual(res.status_code, 403)
