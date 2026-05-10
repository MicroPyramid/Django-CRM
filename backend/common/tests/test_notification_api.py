"""End-to-end tests for the in-app notifications REST surface.

Mirrors the request flow from the SvelteKit frontend: JWT in Authorization
header, no special org header, recipient filter enforced server-side.
"""

from datetime import timedelta
from urllib.parse import urlencode

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from common.models import Notification, Org, Profile, User
from common.serializer import OrgAwareRefreshToken


class NotificationAPIBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org_a = Org.objects.create(name="Org A")
        cls.org_b = Org.objects.create(name="Org B")
        cls.user_a = User.objects.create_user(email="a@test.com", password="x")
        cls.user_b = User.objects.create_user(email="b@test.com", password="x")
        cls.profile_a = Profile.objects.create(
            user=cls.user_a, org=cls.org_a, role="USER", is_active=True
        )
        cls.profile_b = Profile.objects.create(
            user=cls.user_b, org=cls.org_b, role="USER", is_active=True
        )

    def setUp(self):
        self.client = APIClient()
        token = OrgAwareRefreshToken.for_user_and_org(self.user_a, self.org_a)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def _bulk(self, profile, n, **kw):
        return [
            Notification.objects.create(
                org=profile.org, recipient=profile, verb=f"v{i}", **kw
            )
            for i in range(n)
        ]


class TestList(NotificationAPIBase):
    def test_unauthenticated_rejected(self):
        anon = APIClient()
        r = anon.get("/api/notifications/")
        # DRF returns 401 when an auth scheme advertises WWW-Authenticate;
        # this stack returns 403 because no credential was attempted at all.
        assert r.status_code in (401, 403)

    def test_empty_list(self):
        r = self.client.get("/api/notifications/")
        assert r.status_code == 200
        data = r.json()
        assert data == {"count": 0, "unread_count": 0, "results": []}

    def test_list_returns_only_my_notifications(self):
        self._bulk(self.profile_a, 2)
        # Other user's row should never leak
        Notification.objects.create(
            org=self.org_b, recipient=self.profile_b, verb="other"
        )
        r = self.client.get("/api/notifications/")
        data = r.json()
        assert data["count"] == 2
        assert data["unread_count"] == 2
        verbs = [row["verb"] for row in data["results"]]
        assert "other" not in verbs

    def test_unread_filter(self):
        rows = self._bulk(self.profile_a, 3)
        rows[0].read_at = timezone.now()
        rows[0].save(update_fields=["read_at"])
        r = self.client.get("/api/notifications/?unread=true")
        data = r.json()
        assert data["count"] == 2
        assert data["unread_count"] == 2

    def test_since_filter(self):
        n1 = Notification.objects.create(
            org=self.org_a, recipient=self.profile_a, verb="old"
        )
        # Backdate it
        Notification.objects.filter(pk=n1.pk).update(
            created_at=timezone.now() - timedelta(hours=2)
        )
        Notification.objects.create(
            org=self.org_a, recipient=self.profile_a, verb="new"
        )
        cutoff = (timezone.now() - timedelta(hours=1)).isoformat()
        r = self.client.get("/api/notifications/?" + urlencode({"since": cutoff}))
        data = r.json()
        assert data["count"] == 1
        assert data["results"][0]["verb"] == "new"
        # unread_count is the *global* unread, not since-scoped
        assert data["unread_count"] == 2

    def test_limit_clamps_to_max(self):
        self._bulk(self.profile_a, 3)
        r = self.client.get("/api/notifications/?limit=2")
        data = r.json()
        assert data["count"] == 3  # total still 3
        assert len(data["results"]) == 2  # but only 2 returned

    def test_results_newest_first(self):
        first = Notification.objects.create(
            org=self.org_a, recipient=self.profile_a, verb="first"
        )
        Notification.objects.filter(pk=first.pk).update(
            created_at=timezone.now() - timedelta(seconds=10)
        )
        Notification.objects.create(
            org=self.org_a, recipient=self.profile_a, verb="second"
        )
        r = self.client.get("/api/notifications/")
        verbs = [row["verb"] for row in r.json()["results"]]
        assert verbs == ["second", "first"]


class TestMarkRead(NotificationAPIBase):
    def test_mark_read_sets_read_at(self):
        n = Notification.objects.create(
            org=self.org_a, recipient=self.profile_a, verb="x"
        )
        r = self.client.post(f"/api/notifications/{n.id}/read/")
        assert r.status_code == 204
        n.refresh_from_db()
        assert n.read_at is not None

    def test_mark_read_idempotent(self):
        n = Notification.objects.create(
            org=self.org_a,
            recipient=self.profile_a,
            verb="x",
            read_at=timezone.now() - timedelta(hours=1),
        )
        first = n.read_at
        r = self.client.post(f"/api/notifications/{n.id}/read/")
        assert r.status_code == 204
        n.refresh_from_db()
        # Re-marking should not move read_at backwards or forwards
        assert n.read_at == first

    def test_cannot_mark_read_other_users_notification(self):
        n = Notification.objects.create(
            org=self.org_b, recipient=self.profile_b, verb="x"
        )
        r = self.client.post(f"/api/notifications/{n.id}/read/")
        assert r.status_code == 404
        n.refresh_from_db()
        assert n.read_at is None


class TestReadAll(NotificationAPIBase):
    def test_marks_all_unread_read(self):
        rows = self._bulk(self.profile_a, 3)
        r = self.client.post("/api/notifications/read-all/")
        assert r.status_code == 204
        for row in rows:
            row.refresh_from_db()
            assert row.read_at is not None

    def test_before_cutoff_skips_newer(self):
        old = Notification.objects.create(
            org=self.org_a, recipient=self.profile_a, verb="old"
        )
        Notification.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timedelta(hours=2)
        )
        new = Notification.objects.create(
            org=self.org_a, recipient=self.profile_a, verb="new"
        )
        cutoff = (timezone.now() - timedelta(hours=1)).isoformat()
        r = self.client.post(
            "/api/notifications/read-all/",
            {"before": cutoff},
            format="json",
        )
        assert r.status_code == 204
        old.refresh_from_db()
        new.refresh_from_db()
        assert old.read_at is not None
        assert new.read_at is None

    def test_does_not_touch_other_users(self):
        n_other = Notification.objects.create(
            org=self.org_b, recipient=self.profile_b, verb="other"
        )
        self.client.post("/api/notifications/read-all/")
        n_other.refresh_from_db()
        assert n_other.read_at is None


class TestDelete(NotificationAPIBase):
    def test_delete_my_notification(self):
        n = Notification.objects.create(
            org=self.org_a, recipient=self.profile_a, verb="x"
        )
        r = self.client.delete(f"/api/notifications/{n.id}/")
        assert r.status_code == 204
        assert not Notification.objects.filter(pk=n.id).exists()

    def test_cannot_delete_other_users_notification(self):
        n = Notification.objects.create(
            org=self.org_b, recipient=self.profile_b, verb="x"
        )
        r = self.client.delete(f"/api/notifications/{n.id}/")
        assert r.status_code == 404
        assert Notification.objects.filter(pk=n.id).exists()
