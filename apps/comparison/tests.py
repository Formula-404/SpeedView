import json
from uuid import UUID
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.user.models import UserProfile
from apps.team.models import Team
from .models import Comparison, ComparisonTeam
from . import views as comparison_viewshttps://helven-marcia-speedview.pbp.cs.ui.ac.id/team/


def make_user(username="user", password="pass12345", role="user"):
    User = get_user_model()
    u = User.objects.create_user(username=username, password=password, email=f"{username}@x.test")
    UserProfile.objects.create(id=u, role=("admin" if role == "admin" else "user"), theme_preference="dark")
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


class ComparisonPagesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = make_user("owner", role="user")
        self.other = make_user("other", role="user")
        self.admin = make_user("admin", role="admin")

        self.t1 = Team.objects.create(team_name="Ferrari", team_colour="FF0000")
        self.t2 = Team.objects.create(team_name="McLaren", team_colour="FF8000")

        self.private_cmp = Comparison.objects.create(
            owner=self.owner, module=Comparison.MODULE_TEAM, title="Private", is_public=False
        )
        ComparisonTeam.objects.create(comparison=self.private_cmp, team=self.t1, order_index=0)
        ComparisonTeam.objects.create(comparison=self.private_cmp, team=self.t2, order_index=1)

        self.public_cmp = Comparison.objects.create(
            owner=self.owner, module=Comparison.MODULE_TEAM, title="Public", is_public=True
        )
        ComparisonTeam.objects.create(comparison=self.public_cmp, team=self.t1, order_index=0)
        ComparisonTeam.objects.create(comparison=self.public_cmp, team=self.t2, order_index=1)

    def test_list_page_accessible_to_guests(self):
        url = reverse("comparison:list_page")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_create_page_requires_login(self):
        url = reverse("comparison:create_page")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)

    def test_detail_page_requires_login(self):
        url = reverse("comparison:detail_page", kwargs={"pk": self.public_cmp.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)

    def test_detail_page_owner_sees_private(self):
        self.client.login(username=self.owner.username, password="pass12345")
        url = reverse("comparison:detail_page", kwargs={"pk": self.private_cmp.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_detail_page_other_user_public_allowed(self):
        self.client.login(username=self.other.username, password="pass12345")
        url = reverse("comparison:detail_page", kwargs={"pk": self.public_cmp.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)


class ComparisonApiListTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = make_user("owner", role="user")
        self.other = make_user("other", role="user")

        self.t1 = Team.objects.create(team_name="Ferrari", team_colour="FF0000")
        self.t2 = Team.objects.create(team_name="McLaren", team_colour="FF8000")

        self.public_cmp = Comparison.objects.create(
            owner=self.owner, module=Comparison.MODULE_TEAM, title="Public", is_public=True
        )
        ComparisonTeam.objects.create(comparison=self.public_cmp, team=self.t1, order_index=0)
        ComparisonTeam.objects.create(comparison=self.public_cmp, team=self.t2, order_index=1)

        self.private_cmp = Comparison.objects.create(
            owner=self.owner, module=Comparison.MODULE_TEAM, title="Private", is_public=False
        )
        ComparisonTeam.objects.create(comparison=self.private_cmp, team=self.t2, order_index=0)
        ComparisonTeam.objects.create(comparison=self.private_cmp, team=self.t1, order_index=1)

    def test_api_list_guest_sees_only_public(self):
        url = reverse("comparison:api_list") + "?scope=all"
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertTrue(payload["ok"])
        titles = [d["title"] for d in payload["data"]]
        self.assertIn("Public", titles)
        self.assertNotIn("Private", titles)

        pub = next(d for d in payload["data"] if d["title"] == "Public")
        self.assertEqual(pub["items"], ["Ferrari", "McLaren"])

    def test_api_list_authenticated_all_includes_own_private(self):
        self.client.login(username=self.owner.username, password="pass12345")
        url = reverse("comparison:api_list") + "?scope=all"
        res = self.client.get(url)
        payload = res.json()
        titles = [d["title"] for d in payload["data"]]
        self.assertIn("Public", titles)
        self.assertIn("Private", titles)

    def test_api_list_my_scope_only_owner_items(self):
        self.client.login(username=self.owner.username, password="pass12345")
        url = reverse("comparison:api_list") + "?scope=my"
        res = self.client.get(url)
        payload = res.json()
        self.assertTrue(payload["ok"])
        self.assertGreaterEqual(payload["count"], 2)
        self.assertTrue(all(d["owner_name"] == self.owner.username for d in payload["data"]))

    def test_api_list_my_scope_guest_gets_empty(self):
        url = reverse("comparison:api_list") + "?scope=my"
        res = self.client.get(url)
        payload = res.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["count"], 0)


class ComparisonApiCreateDetailDeleteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.owner = make_user("owner", role="user")
        self.other = make_user("other", role="user")
        self.admin = make_user("admin", role="admin")

        self.t1 = Team.objects.create(team_name="Ferrari", team_colour="FF0000")
        self.t2 = Team.objects.create(team_name="McLaren", team_colour="FF8000")
        self.t3 = Team.objects.create(team_name="Red Bull Racing", team_colour="00A19A")

    def test_api_create_requires_login(self):
        url = reverse("comparison:api_create")
        res = self.client.post(url, data=json.dumps({}), content_type="application/json")
        self.assertEqual(res.status_code, 302)
        
    def test_api_detail_owner_only(self):
        cmp = Comparison.objects.create(owner=self.owner, module=Comparison.MODULE_TEAM, title="Mine", is_public=False)
        ComparisonTeam.objects.create(comparison=cmp, team=self.t1, order_index=0)
        ComparisonTeam.objects.create(comparison=cmp, team=self.t2, order_index=1)

        self.client.login(username=self.owner.username, password="pass12345")
        url = reverse("comparison:api_detail", kwargs={"pk": cmp.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["data"]["module"], "team")
        self.assertEqual([it["team_name"] for it in data["data"]["items"]], ["Ferrari", "McLaren"])

        self.client.logout()
        self.client.login(username=self.other.username, password="pass12345")
        res2 = self.client.get(url)
        self.assertEqual(res2.status_code, 404)

    def test_api_delete_owner_or_admin_only(self):
        cmp = Comparison.objects.create(owner=self.owner, module=Comparison.MODULE_TEAM, title="Del", is_public=False)
        url = reverse("comparison:api_delete", kwargs={"pk": cmp.pk})

        self.client.login(username=self.other.username, password="pass12345")
        res = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest", HTTP_ACCEPT="application/json")
        self.assertEqual(res.status_code, 403)
        self.assertTrue(Comparison.objects.filter(pk=cmp.pk).exists())

        self.client.logout()
        self.client.login(username=self.owner.username, password="pass12345")
        res2 = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest", HTTP_ACCEPT="application/json")
        self.assertEqual(res2.status_code, 200)
        self.assertFalse(Comparison.objects.filter(pk=cmp.pk).exists())

        cmp2 = Comparison.objects.create(owner=self.owner, module=Comparison.MODULE_TEAM, title="Del2", is_public=False)
        self.client.logout()
        self.client.login(username=self.admin.username, password="pass12345")
        url2 = reverse("comparison:api_delete", kwargs={"pk": cmp2.pk})
        res3 = self.client.post(url2, HTTP_X_REQUESTED_WITH="XMLHttpRequest", HTTP_ACCEPT="application/json")
        self.assertEqual(res3.status_code, 200)
        self.assertFalse(Comparison.objects.filter(pk=cmp2.pk).exists())

    def test_model_str_and_get_absolute_url(self):
        cmp = Comparison.objects.create(owner=self.owner, module=Comparison.MODULE_TEAM, title="URL", is_public=True)
        s = str(cmp)
        self.assertIn("team comparison", s)
        url = cmp.get_absolute_url()
        self.assertTrue(str(cmp.pk) in url)
        UUID(str(cmp.pk)) 
