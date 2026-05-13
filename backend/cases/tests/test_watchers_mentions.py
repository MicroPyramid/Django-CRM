"""Mention parser + comment-driven notification dispatch tests."""

import pytest
from datetime import timedelta
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from cases.models import Case, CaseWatcher
from cases.notifications import (
    MENTION_RE,
    dispatch_for_comment,
    parse_mentions,
    resolve_mentions,
)
from common.models import Comment, Notification, Profile, User


def _make_profile(org, *, email):
    user, _ = User.objects.get_or_create(email=email, defaults={"password": "x"})
    return Profile.objects.create(user=user, org=org, role="USER", is_active=True)


def _comment(case, body, by):
    return Comment.objects.create(
        comment=body,
        content_type=ContentType.objects.get_for_model(Case),
        object_id=case.id,
        commented_by=by,
        org=case.org,
    )


@pytest.mark.django_db
class TestParseMentions:
    def test_basic_mention(self):
        assert parse_mentions("hey @alice please look") == ["alice"]

    def test_multiple_unique_lowercase(self):
        out = parse_mentions("@Bob @alice @bob")
        # de-duped, lowered, order preserved
        assert out == ["bob", "alice"]

    def test_does_not_match_email_addresses(self):
        # The @ in 'foo@bar.com' is preceded by an alphanumeric — should be skipped.
        assert parse_mentions("send mail to alice@example.com") == []

    def test_punctuation_chars_in_username(self):
        assert parse_mentions("ping @first.last and @x_y-z") == [
            "first.last",
            "x_y-z",
        ]

    def test_no_match_inside_word(self):
        # `\u`@x` — preceded by alphanumeric, skip
        assert parse_mentions("u@x") == []

    def test_empty_body(self):
        assert parse_mentions("") == []
        assert parse_mentions(None) == []


@pytest.mark.django_db
class TestResolveMentions:
    def test_resolves_email_local_part(self, org_a):
        p = _make_profile(org_a, email="alice@example.com")
        out = resolve_mentions(["alice"], org_a.id)
        assert out == [p]

    def test_unresolved_dropped(self, org_a):
        _make_profile(org_a, email="alice@example.com")
        out = resolve_mentions(["bob"], org_a.id)
        assert out == []

    def test_does_not_cross_org(self, org_a, org_b):
        _make_profile(org_a, email="alice@a.com")
        p_b = _make_profile(org_b, email="alice@b.com")
        out = resolve_mentions(["alice"], org_a.id)
        # Should match the org_a profile, never the org_b one even though
        # they share a username.
        assert len(out) == 1
        assert out[0].org_id == org_a.id
        assert out[0].id != p_b.id

    def test_inactive_profile_skipped(self, org_a):
        p = _make_profile(org_a, email="alice@x.com")
        p.is_active = False
        p.save()
        assert resolve_mentions(["alice"], org_a.id) == []


@pytest.mark.django_db
class TestDispatchForComment:
    def test_mention_creates_notification_and_auto_watcher(
        self, case_a, admin_profile, org_a
    ):
        bob = _make_profile(org_a, email="bob@org.com")
        c = _comment(case_a, "hey @bob please review", by=admin_profile)

        # Sanity: notifications were dispatched via the signal handler.
        assert Notification.objects.filter(
            recipient=bob, verb="case.mentioned"
        ).count() == 1
        # Auto-watch row.
        watch = CaseWatcher.objects.get(case=case_a, profile=bob)
        assert watch.subscribed_via == "mention"

    def test_actor_is_not_self_mentioned(self, case_a, admin_profile, org_a):
        # admin's email local-part is "admin"
        c = _comment(case_a, "I'm just thinking out loud @admin", by=admin_profile)
        assert not Notification.objects.filter(
            recipient=admin_profile, verb="case.mentioned"
        ).exists()

    def test_unknown_username_silently_ignored(
        self, case_a, admin_profile
    ):
        _comment(case_a, "@nosuchuser ping?", by=admin_profile)
        # No new mention notifications, no extra watcher rows
        assert Notification.objects.filter(verb="case.mentioned").count() == 0

    def test_email_addresses_in_body_do_not_create_mentions(
        self, case_a, admin_profile, org_a
    ):
        bob = _make_profile(org_a, email="bob@org.com")
        _comment(
            case_a, "Sent to bob@org.com about this", by=admin_profile
        )
        # @ preceded by alphanumeric — must NOT be parsed as a mention.
        assert not Notification.objects.filter(
            recipient=bob, verb="case.mentioned"
        ).exists()

    def test_mention_rate_limited_per_recipient_per_case(
        self, case_a, admin_profile, org_a
    ):
        bob = _make_profile(org_a, email="bob@org.com")
        _comment(case_a, "@bob first", by=admin_profile)
        # Second mention within the rate-limit window should be skipped.
        _comment(case_a, "@bob again immediately", by=admin_profile)
        assert Notification.objects.filter(
            recipient=bob, verb="case.mentioned"
        ).count() == 1

    def test_mention_rate_limit_does_not_block_after_window(
        self, case_a, admin_profile, org_a
    ):
        bob = _make_profile(org_a, email="bob@org.com")
        first = _comment(case_a, "@bob first", by=admin_profile)
        # Move the prior notification's created_at back 2 minutes.
        Notification.objects.filter(recipient=bob, verb="case.mentioned").update(
            created_at=timezone.now() - timedelta(minutes=2)
        )
        _comment(case_a, "@bob again", by=admin_profile)
        assert Notification.objects.filter(
            recipient=bob, verb="case.mentioned"
        ).count() == 2

    def test_watchers_get_case_commented_notification(
        self, case_a, admin_profile, org_a
    ):
        watcher = _make_profile(org_a, email="watcher@org.com")
        CaseWatcher.objects.create(case=case_a, profile=watcher, org=org_a)

        _comment(case_a, "important update", by=admin_profile)

        assert Notification.objects.filter(
            recipient=watcher, verb="case.commented"
        ).count() == 1

    def test_actor_does_not_get_their_own_comment_notification(
        self, case_a, admin_profile, org_a
    ):
        # Actor is also a watcher — should still NOT receive case.commented.
        CaseWatcher.objects.create(
            case=case_a, profile=admin_profile, org=org_a
        )
        _comment(case_a, "self note", by=admin_profile)
        assert not Notification.objects.filter(
            recipient=admin_profile, verb="case.commented"
        ).exists()

    def test_mentioned_user_does_not_also_get_case_commented(
        self, case_a, admin_profile, org_a
    ):
        bob = _make_profile(org_a, email="bob@org.com")
        # Pre-existing watch shouldn't double up either.
        CaseWatcher.objects.create(case=case_a, profile=bob, org=org_a)
        _comment(case_a, "@bob look at this", by=admin_profile)
        assert Notification.objects.filter(
            recipient=bob, verb="case.mentioned"
        ).count() == 1
        assert not Notification.objects.filter(
            recipient=bob, verb="case.commented"
        ).exists()
