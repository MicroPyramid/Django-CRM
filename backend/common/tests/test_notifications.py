"""Tests for the Notification model and dispatcher (`common.notifications`).

API-level coverage lives in `test_notification_api.py` once that lands.
"""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import Account
from common import notifications
from common.models import Notification, Org, Profile, User
from conftest import set_rls_context


class NotificationModelBase(TestCase):
    def setUp(self):
        # These classes build their own orgs rather than taking the `org_a`
        # fixture, so nothing has set `app.current_org` for them. `notification`
        # is org-scoped, and under a role RLS binds its insert check refuses a
        # write made with no context. Per-test rather than in `setUpTestData`
        # because a session-level `set_config` is undone when the surrounding
        # transaction rolls back, which is exactly what `TestCase` does.
        set_rls_context(self.org_a)

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
        qs = Notification.objects.filter(recipient=self.profile_a, read_at__isnull=True)
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
    def test_create_writes_the_row(self):
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

    def test_create_skips_inactive_recipient(self):
        self.profile_a.is_active = False
        self.profile_a.save()
        n = notifications.create(self.profile_a, "case.commented")
        assert n is None
        assert not Notification.objects.filter(recipient=self.profile_a).exists()

    def test_create_with_entity_denormalizes_type_id_name(self):
        account = Account.objects.create(name="Acme Corp", org=self.org_a)
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
        n = notifications.create(
            self.profile_a,
            "account.assigned",
            entity=account,
            entity_name="Custom Label",
        )
        assert n.entity_name == "Custom Label"

    def test_create_needs_no_broker(self):
        """The row IS the delivery mechanism.

        `create()` used to publish on Redis for the SSE stream to fan out.
        That stream is gone, so notification delivery must not depend on a
        broker being reachable at all: clients pick the row up on their next
        `?since=` poll. Nothing is patched here on purpose.
        """
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
        # The task walks every org and clears the context on the way out, which
        # is correct: it runs on a pooled connection with no middleware, and
        # leaving the last org's id behind would hand that tenant's context to
        # the next borrower. The assertions below are this test's own reads, so
        # they need the context put back.
        set_rls_context(self.org_a)

        assert deleted == 1
        assert not Notification.objects.filter(pk=old_read.pk).exists()
        assert Notification.objects.filter(pk=recent_read.pk).exists()
        assert Notification.objects.filter(pk=old_unread.pk).exists()

    def test_purge_respects_custom_days_arg(self):
        from common.tasks import purge_read_notifications

        # Read 5 days ago, survives default 90, but not when days=1
        n = Notification.objects.create(
            org=self.org_a,
            recipient=self.profile_a,
            verb="x",
            read_at=timezone.now() - timedelta(days=5),
        )
        assert purge_read_notifications(days=90) == 0
        assert purge_read_notifications(days=1) == 1
        assert not Notification.objects.filter(pk=n.pk).exists()

    def test_purge_sets_rls_context_for_every_org(self):
        """The task must scope itself per org, or it deletes nothing in production.

        `notification` is org-scoped, a Celery worker runs no middleware, and the
        isolation policy matches no rows when `app.current_org` is empty. The
        previous version ran one unscoped DELETE and its tests passed anyway,
        because `crm.test_settings` is SQLite and has no RLS to fail against.
        This asserts the call the SQLite backend cannot: that each org's id is
        pushed into the context before its rows are touched, and that the
        context is cleared at the end rather than left on the connection.
        """
        from unittest import mock

        import common.tasks as tasks_module

        seen = []
        cleared = []

        Notification.objects.create(
            org=self.org_a,
            recipient=self.profile_a,
            verb="x",
            read_at=timezone.now() - timedelta(days=120),
        )
        with (
            mock.patch.object(
                tasks_module,
                "set_rls_context",
                side_effect=lambda org_id: seen.append(str(org_id)),
            ),
            mock.patch.object(
                tasks_module,
                "clear_rls_context",
                side_effect=lambda: cleared.append(True),
            ),
        ):
            tasks_module.purge_read_notifications()

        assert str(self.org_a.id) in seen
        assert str(self.org_b.id) in seen
        assert cleared == [True]
