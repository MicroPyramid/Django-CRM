"""Tests for the Notification model and dispatcher (`common.notifications`).

API-level coverage lives in `test_notification_api.py` once that lands.
"""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from accounts.models import Account
from common import notifications
from common.models import Notification, Org, Profile, User


class NotificationModelBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org_a = Org.objects.create(name="Org A")
        cls.org_b = Org.objects.create(name="Org B")
        cls.user_a = User.objects.create_user(email="a@test.com", password="x")
        cls.user_b = User.objects.create_user(email="b@test.com", password="x")
        cls.actor = User.objects.create_user(email="actor@test.com", password="x")
        cls.profile_a = Profile.objects.create(
            user=cls.user_a, org=cls.org_a, role="USER", is_active=True
        )
        cls.profile_b = Profile.objects.create(
            user=cls.user_b, org=cls.org_b, role="USER", is_active=True
        )
        cls.actor_profile = Profile.objects.create(
            user=cls.actor, org=cls.org_a, role="USER", is_active=True
        )


class TestNotificationModel(NotificationModelBase):
    def test_create_minimal(self):
        notif = Notification.objects.create(
            org=self.org_a,
            recipient=self.profile_a,
            verb="case.commented",
        )
        assert notif.id is not None
        assert notif.read_at is None
        assert notif.data == {}
        assert notif.entity_type == ""
        assert notif.link == ""
        assert notif.actor is None

    def test_str_includes_verb_and_recipient(self):
        n = Notification.objects.create(
            org=self.org_a, recipient=self.profile_a, verb="case.mentioned"
        )
        s = str(n)
        assert "case.mentioned" in s
        assert str(self.profile_a.id) in s

    def test_unread_filter(self):
        unread = Notification.objects.create(
            org=self.org_a, recipient=self.profile_a, verb="case.assigned"
        )
        read = Notification.objects.create(
            org=self.org_a,
            recipient=self.profile_a,
            verb="case.assigned",
            read_at=timezone.now(),
        )
        qs = Notification.objects.filter(
            recipient=self.profile_a, read_at__isnull=True
        )
        ids = list(qs.values_list("id", flat=True))
        assert unread.id in ids
        assert read.id not in ids

    def test_ordering_newest_first(self):
        first = Notification.objects.create(
            org=self.org_a, recipient=self.profile_a, verb="v1"
        )
        # Force a distinct created_at
        Notification.objects.filter(pk=first.pk).update(
            created_at=timezone.now() - timedelta(seconds=10)
        )
        second = Notification.objects.create(
            org=self.org_a, recipient=self.profile_a, verb="v2"
        )
        ids = list(
            Notification.objects.filter(recipient=self.profile_a).values_list(
                "id", flat=True
            )
        )
        assert ids[0] == second.id
        assert ids[1] == first.id

    def test_actor_set_null_on_actor_delete(self):
        n = Notification.objects.create(
            org=self.org_a,
            recipient=self.profile_a,
            actor=self.actor_profile,
            verb="case.mentioned",
        )
        self.actor_profile.delete()
        n.refresh_from_db()
        assert n.actor_id is None

    def test_recipient_cascade_on_profile_delete(self):
        n = Notification.objects.create(
            org=self.org_a, recipient=self.profile_a, verb="case.assigned"
        )
        nid = n.id
        self.profile_a.delete()
        assert not Notification.objects.filter(pk=nid).exists()


class TestDispatcher(NotificationModelBase):
    def test_create_writes_row_and_publishes(self):
        with patch("common.notifications._publish") as pub:
            n = notifications.create(
                self.profile_a,
                "case.commented",
                actor=self.actor_profile,
                link="/cases/123",
                data={"comment_excerpt": "hello"},
            )
        assert n is not None
        assert n.org_id == self.org_a.id
        assert n.recipient_id == self.profile_a.id
        assert n.actor_id == self.actor_profile.id
        assert n.link == "/cases/123"
        assert n.data == {"comment_excerpt": "hello"}
        pub.assert_called_once()
        channel, payload = pub.call_args[0]
        assert channel == f"notif:{self.org_a.id}:{self.profile_a.id}"
        assert payload == str(n.id)

    def test_create_skips_inactive_recipient(self):
        self.profile_a.is_active = False
        self.profile_a.save()
        with patch("common.notifications._publish") as pub:
            n = notifications.create(self.profile_a, "case.commented")
        assert n is None
        pub.assert_not_called()
        assert not Notification.objects.filter(recipient=self.profile_a).exists()

    def test_create_with_entity_denormalizes_type_id_name(self):
        account = Account.objects.create(name="Acme Corp", org=self.org_a)
        with patch("common.notifications._publish"):
            n = notifications.create(
                self.profile_a,
                "account.assigned",
                entity=account,
            )
        assert n.entity_type == "Account"
        assert n.entity_id == account.pk
        assert n.entity_name == "Acme Corp"

    def test_create_entity_name_override(self):
        account = Account.objects.create(name="Acme Corp", org=self.org_a)
        with patch("common.notifications._publish"):
            n = notifications.create(
                self.profile_a,
                "account.assigned",
                entity=account,
                entity_name="Custom Label",
            )
        assert n.entity_name == "Custom Label"

    def test_create_does_not_raise_when_redis_publish_fails(self):
        # Simulate redis being totally broken.
        with patch("common.notifications._get_redis") as gr:
            gr.return_value = type(
                "_BrokenClient",
                (),
                {"publish": lambda self, *a, **kw: (_ for _ in ()).throw(RuntimeError("boom"))},
            )()
            # Should NOT raise — publish is best-effort.
            n = notifications.create(self.profile_a, "case.commented")
        assert n is not None
        assert Notification.objects.filter(pk=n.pk).exists()


class TestPurgeTask(NotificationModelBase):
    def test_purges_only_read_rows_older_than_cutoff(self):
        from common.tasks import purge_read_notifications

        old_read = Notification.objects.create(
            org=self.org_a,
            recipient=self.profile_a,
            verb="x",
            read_at=timezone.now() - timedelta(days=120),
        )
        # Backdate read_at to be older than 90 days
        Notification.objects.filter(pk=old_read.pk).update(
            read_at=timezone.now() - timedelta(days=120)
        )
        recent_read = Notification.objects.create(
            org=self.org_a,
            recipient=self.profile_a,
            verb="x",
            read_at=timezone.now() - timedelta(days=10),
        )
        old_unread = Notification.objects.create(
            org=self.org_a, recipient=self.profile_a, verb="x"
        )
        Notification.objects.filter(pk=old_unread.pk).update(
            created_at=timezone.now() - timedelta(days=400)
        )

        deleted = purge_read_notifications()
        assert deleted == 1
        assert not Notification.objects.filter(pk=old_read.pk).exists()
        assert Notification.objects.filter(pk=recent_read.pk).exists()
        assert Notification.objects.filter(pk=old_unread.pk).exists()

    def test_purge_respects_custom_days_arg(self):
        from common.tasks import purge_read_notifications

        # Read 5 days ago — survives default 90, but not when days=1
        n = Notification.objects.create(
            org=self.org_a,
            recipient=self.profile_a,
            verb="x",
            read_at=timezone.now() - timedelta(days=5),
        )
        assert purge_read_notifications(days=90) == 0
        assert purge_read_notifications(days=1) == 1
        assert not Notification.objects.filter(pk=n.pk).exists()
