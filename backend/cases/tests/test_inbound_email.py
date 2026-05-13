"""Inbound email pipeline tests: parser, spam filter, threading, pipeline, API.

See docs/cases/tier1/email-to-ticket.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from cases.inbound.parser import ParsedEmail, parse_raw_email
from cases.inbound.pipeline import ingest
from cases.inbound.spam import should_drop
from cases.inbound.threading import find_existing_case, short_case_id
from cases.models import Case, EmailMessage, InboundMailbox
from common.models import Profile, User
from contacts.models import Contact

MAILBOXES_URL = "/api/cases/mailboxes/"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mailbox(org, **overrides):
    defaults = {
        "address": "support@acme.com",
        "provider": "ses",
        "webhook_secret": "test-secret",
        "default_priority": "Normal",
        "default_case_type": None,
        "is_active": True,
    }
    defaults.update(overrides)
    return InboundMailbox.objects.create(org=org, **defaults)


def _raw_email(
    *,
    message_id="<m1@example.com>",
    in_reply_to="",
    references="",
    from_="Customer <user@example.com>",
    to="support@acme.com",
    subject="Help with login",
    body="I cannot log in.",
    extra_headers="",
):
    headers = [
        f"From: {from_}",
        f"To: {to}",
        f"Subject: {subject}",
        "Date: Sat, 9 May 2026 12:00:00 +0000",
        f"Message-ID: {message_id}",
    ]
    if in_reply_to:
        headers.append(f"In-Reply-To: {in_reply_to}")
    if references:
        headers.append(f"References: {references}")
    if extra_headers:
        headers.append(extra_headers)
    headers.append("MIME-Version: 1.0")
    headers.append('Content-Type: text/plain; charset="utf-8"')
    return "\r\n".join(headers) + "\r\n\r\n" + body


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestParser:
    def test_basic_headers_and_body(self):
        parsed = parse_raw_email(_raw_email())
        assert parsed.message_id == "m1@example.com"
        assert parsed.from_address == "user@example.com"
        assert parsed.from_display_name == "Customer"
        assert "support@acme.com" in parsed.to_addresses
        assert parsed.subject == "Help with login"
        assert "I cannot log in" in parsed.body_text

    def test_in_reply_to_and_references(self):
        parsed = parse_raw_email(
            _raw_email(
                message_id="<m2@example.com>",
                in_reply_to="<m1@example.com>",
                references="<m0@example.com> <m1@example.com>",
            )
        )
        assert parsed.in_reply_to == "m1@example.com"
        assert parsed.references == ["m0@example.com", "m1@example.com"]

    def test_strips_angle_brackets(self):
        parsed = parse_raw_email(_raw_email(message_id="<has-angles@x>"))
        assert parsed.message_id == "has-angles@x"

    def test_bounce_detection(self):
        # multipart/report with delivery-status report-type → bounce
        bounce = (
            "From: MAILER-DAEMON@example.com\r\n"
            "To: support@acme.com\r\n"
            "Subject: Delivery Status Notification\r\n"
            "Date: Sat, 9 May 2026 12:00:00 +0000\r\n"
            "Message-ID: <bounce@x>\r\n"
            "MIME-Version: 1.0\r\n"
            'Content-Type: multipart/report; report-type=delivery-status; '
            'boundary="b"\r\n'
            "\r\n"
            "--b\r\n"
            "Content-Type: text/plain\r\n\r\n"
            "Delivery failed.\r\n"
            "--b--\r\n"
        )
        parsed = parse_raw_email(bounce)
        assert parsed.is_bounce is True


# ---------------------------------------------------------------------------
# Spam filter
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSpam:
    def test_passes_normal_mail(self):
        parsed = parse_raw_email(_raw_email())
        drop, reason = should_drop(parsed)
        assert drop is False and reason == ""

    def test_drops_auto_submitted(self):
        parsed = parse_raw_email(_raw_email(extra_headers="Auto-Submitted: auto-replied"))
        drop, reason = should_drop(parsed)
        assert drop is True and reason == "auto_submitted"

    def test_drops_precedence_bulk(self):
        parsed = parse_raw_email(_raw_email(extra_headers="Precedence: bulk"))
        drop, reason = should_drop(parsed)
        assert drop is True and reason == "precedence_bulk"

    def test_drops_x_autoreply(self):
        parsed = parse_raw_email(_raw_email(extra_headers="X-Autoreply: yes"))
        drop, reason = should_drop(parsed)
        assert drop is True and reason == "x_autoreply"

    def test_drops_mailing_list(self):
        parsed = parse_raw_email(
            _raw_email(
                extra_headers="List-Id: <newsletter.example.com>\r\n"
                "List-Unsubscribe: <mailto:unsub@example.com>"
            )
        )
        drop, reason = should_drop(parsed)
        assert drop is True and reason == "mailing_list"

    def test_drops_bounce(self):
        parsed = ParsedEmail(
            raw_headers={},
            message_id="b@x",
            in_reply_to="",
            references=[],
            from_address="MAILER-DAEMON@example.com",
            from_display_name="",
            to_addresses=[],
            cc_addresses=[],
            subject="",
            body_text="",
            body_html="",
            received_at=datetime.now(timezone.utc),
            is_bounce=True,
        )
        drop, reason = should_drop(parsed)
        assert drop is True and reason == "bounce"


# ---------------------------------------------------------------------------
# Threading
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestThreading:
    def test_in_reply_to_match(self, admin_user, org_a):
        case = Case.objects.create(
            name="Original", status="New", priority="Normal",
            org=org_a, created_by=admin_user, external_thread_id="root@x",
        )
        EmailMessage.objects.create(
            org=org_a, case=case, direction="inbound",
            message_id="root@x", from_address="user@x.com",
            received_at=datetime.now(timezone.utc),
        )
        parsed = parse_raw_email(_raw_email(message_id="<reply@x>", in_reply_to="<root@x>"))
        assert find_existing_case(parsed, org_a) == case

    def test_references_match(self, admin_user, org_a):
        case = Case.objects.create(
            name="Original", status="New", priority="Normal",
            org=org_a, created_by=admin_user, external_thread_id="root@x",
        )
        parsed = parse_raw_email(
            _raw_email(message_id="<reply@x>", references="<root@x> <other@x>")
        )
        assert find_existing_case(parsed, org_a) == case

    def test_no_match_returns_none(self, admin_user, org_a):
        parsed = parse_raw_email(_raw_email(message_id="<lonely@x>"))
        assert find_existing_case(parsed, org_a) is None

    def test_subject_fallback(self, admin_user, org_a):
        case = Case.objects.create(
            name="Original", status="New", priority="Normal",
            org=org_a, created_by=admin_user,
        )
        prefix = short_case_id(case)
        parsed = parse_raw_email(
            _raw_email(
                message_id="<reply@x>",
                subject=f"Re: [Case #{prefix}] Help",
            )
        )
        assert find_existing_case(parsed, org_a) == case

    def test_subject_only_no_brackets_no_match(self, admin_user, org_a):
        case = Case.objects.create(
            name="Help", status="New", priority="Normal",
            org=org_a, created_by=admin_user,
        )
        # Subject identical but no `[Case #...]` marker — must not match.
        parsed = parse_raw_email(_raw_email(message_id="<reply@x>", subject="Help"))
        assert find_existing_case(parsed, org_a) is None

    def test_cross_org_isolation(self, admin_user, org_a, org_b):
        Case.objects.create(
            name="org-a", status="New", priority="Normal",
            org=org_a, created_by=admin_user, external_thread_id="x@x",
        )
        parsed = parse_raw_email(_raw_email(message_id="<reply@x>", in_reply_to="<x@x>"))
        # Looking up against org_b should miss
        assert find_existing_case(parsed, org_b) is None


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPipeline:
    def test_first_email_creates_case_and_contact(self, org_a):
        mailbox = _make_mailbox(org_a, default_priority="High")
        parsed = parse_raw_email(_raw_email())
        result = ingest(parsed, mailbox)
        assert result.created_case is True and result.dropped is False
        assert result.case is not None
        assert result.case.priority == "High"
        assert result.case.external_thread_id == "m1@example.com"
        # Contact auto-created
        contact = Contact.objects.get(email__iexact="user@example.com", org=org_a)
        assert contact.auto_created is True
        assert contact.first_name == "Customer"
        assert result.case.contacts.filter(pk=contact.pk).exists()
        # EmailMessage row recorded with the case
        em = EmailMessage.objects.get(message_id="m1@example.com", org=org_a)
        assert em.case_id == result.case.id

    def test_reply_threads_to_existing(self, org_a):
        mailbox = _make_mailbox(org_a)
        first = parse_raw_email(_raw_email())
        first_result = ingest(first, mailbox)
        case = first_result.case

        reply = parse_raw_email(
            _raw_email(message_id="<m2@example.com>", in_reply_to="<m1@example.com>")
        )
        second_result = ingest(reply, mailbox)
        assert second_result.created_case is False
        assert second_result.case == case
        assert EmailMessage.objects.filter(case=case).count() == 2

    def test_spam_dropped_no_case_created(self, org_a):
        mailbox = _make_mailbox(org_a)
        parsed = parse_raw_email(_raw_email(extra_headers="Auto-Submitted: auto-replied"))
        result = ingest(parsed, mailbox)
        assert result.dropped is True
        assert result.drop_reason == "auto_submitted"
        assert result.case is None
        assert Case.objects.count() == 0
        em = EmailMessage.objects.get(message_id="m1@example.com")
        assert em.case is None and em.drop_reason == "auto_submitted"

    def test_existing_contact_reused(self, org_a):
        mailbox = _make_mailbox(org_a)
        Contact.objects.create(
            org=org_a,
            email="user@example.com",
            first_name="Existing",
            last_name="User",
            is_active=True,
        )
        parsed = parse_raw_email(_raw_email())
        result = ingest(parsed, mailbox)
        contact = Contact.objects.get(email__iexact="user@example.com", org=org_a)
        assert contact.auto_created is False
        assert contact.first_name == "Existing"
        assert result.case.contacts.filter(pk=contact.pk).exists()

    def test_provider_retry_idempotent(self, org_a):
        mailbox = _make_mailbox(org_a)
        parsed = parse_raw_email(_raw_email())
        first = ingest(parsed, mailbox)
        # Same Message-ID arriving again (provider retry) must not duplicate.
        parsed2 = parse_raw_email(_raw_email())
        second = ingest(parsed2, mailbox)
        assert Case.objects.count() == 1
        assert EmailMessage.objects.filter(message_id="m1@example.com").count() == 1
        assert second.case == first.case
        assert second.created_case is False

    def test_default_assignee_added(self, org_a):
        user = User.objects.create_user(email="agent@x.com", password="x")
        agent = Profile.objects.create(
            user=user, org=org_a, role="USER", is_active=True
        )
        mailbox = _make_mailbox(org_a, default_assignee=agent)
        parsed = parse_raw_email(_raw_email())
        result = ingest(parsed, mailbox)
        assert list(result.case.assigned_to.all()) == [agent]


# ---------------------------------------------------------------------------
# Activity row per inbound email + reopen tie-in
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInboundActivityAndReopen:
    """Item-2 (EMAIL_RECEIVED audit row) and item-1 (reopen on inbound)."""

    def _close(self, case, *, days_ago):
        from datetime import timedelta as _td

        from django.utils import timezone as _tz

        case.status = "Closed"
        case.closed_on = _tz.now().date() - _td(days=days_ago)
        case.save()
        return case

    def _activities(self, case, action):
        from common.models import Activity

        return Activity.objects.filter(
            entity_type="Case", entity_id=case.pk, action=action
        ).order_by("-created_at")

    def test_email_received_activity_emitted_on_new_case(self, org_a):
        mailbox = _make_mailbox(org_a)
        parsed = parse_raw_email(_raw_email())
        result = ingest(parsed, mailbox)
        rows = self._activities(result.case, "EMAIL_RECEIVED")
        assert rows.count() == 1
        meta = rows.first().metadata
        assert meta["from_address"] == "user@example.com"
        assert meta["message_id"] == "m1@example.com"
        assert meta["email_message_id"] == str(result.email_message.pk)

    def test_email_received_activity_emitted_on_threaded_reply(self, org_a):
        mailbox = _make_mailbox(org_a)
        first = ingest(parse_raw_email(_raw_email()), mailbox)
        case = first.case
        ingest(
            parse_raw_email(
                _raw_email(
                    message_id="<m2@example.com>", in_reply_to="<m1@example.com>"
                )
            ),
            mailbox,
        )
        rows = self._activities(case, "EMAIL_RECEIVED")
        assert rows.count() == 2

    def test_email_received_not_emitted_for_drops(self, org_a):
        mailbox = _make_mailbox(org_a)
        parsed = parse_raw_email(
            _raw_email(extra_headers="Auto-Submitted: auto-replied")
        )
        result = ingest(parsed, mailbox)
        assert result.dropped is True
        from common.models import Activity

        assert (
            Activity.objects.filter(action="EMAIL_RECEIVED", org=org_a).count() == 0
        )

    def test_reply_within_window_reopens_closed_case(self, org_a):
        from common.models import Activity

        mailbox = _make_mailbox(org_a)
        first = ingest(parse_raw_email(_raw_email()), mailbox)
        case = first.case
        self._close(case, days_ago=2)

        ingest(
            parse_raw_email(
                _raw_email(
                    message_id="<m2@example.com>", in_reply_to="<m1@example.com>"
                )
            ),
            mailbox,
        )

        case.refresh_from_db()
        assert case.status == "Pending"
        assert case.closed_on is None

        reopened = (
            Activity.objects.filter(
                entity_type="Case", entity_id=case.pk, action="REOPENED"
            )
            .order_by("-created_at")
            .first()
        )
        assert reopened is not None
        assert reopened.metadata["to_status"] == "Pending"
        assert reopened.metadata["days_since_close"] == 2
        assert "email_message_id" in reopened.metadata

    def test_reply_outside_window_does_not_reopen(self, org_a):
        from common.models import Activity

        mailbox = _make_mailbox(org_a)
        first = ingest(parse_raw_email(_raw_email()), mailbox)
        case = first.case
        self._close(case, days_ago=30)

        ingest(
            parse_raw_email(
                _raw_email(
                    message_id="<m2@example.com>", in_reply_to="<m1@example.com>"
                )
            ),
            mailbox,
        )

        case.refresh_from_db()
        assert case.status == "Closed"
        assert (
            Activity.objects.filter(
                entity_type="Case", entity_id=case.pk, action="REOPENED"
            ).count()
            == 0
        )

    def test_reply_to_open_case_does_not_change_status(self, org_a):
        mailbox = _make_mailbox(org_a)
        first = ingest(parse_raw_email(_raw_email()), mailbox)
        case = first.case
        original_status = case.status
        ingest(
            parse_raw_email(
                _raw_email(
                    message_id="<m2@example.com>", in_reply_to="<m1@example.com>"
                )
            ),
            mailbox,
        )
        case.refresh_from_db()
        assert case.status == original_status

    def test_disabled_policy_blocks_reopen(self, org_a):
        from cases.models import ReopenPolicy

        ReopenPolicy.objects.create(org=org_a, is_enabled=False)
        mailbox = _make_mailbox(org_a)
        first = ingest(parse_raw_email(_raw_email()), mailbox)
        case = first.case
        self._close(case, days_ago=1)

        ingest(
            parse_raw_email(
                _raw_email(
                    message_id="<m2@example.com>", in_reply_to="<m1@example.com>"
                )
            ),
            mailbox,
        )
        case.refresh_from_db()
        assert case.status == "Closed"


# ---------------------------------------------------------------------------
# Admin API
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMailboxAPI:
    def test_admin_can_list_and_create(self, admin_client, org_a):
        response = admin_client.get(MAILBOXES_URL)
        assert response.status_code == 200
        assert response.json()["mailboxes"] == []

        create = admin_client.post(
            MAILBOXES_URL,
            {
                "address": "support@acme.com",
                "provider": "ses",
                "default_priority": "High",
            },
            format="json",
        )
        assert create.status_code == 201, create.content
        data = create.json()
        assert data["address"] == "support@acme.com"
        # webhook_secret was auto-generated
        assert data["webhook_secret"]

    def test_user_cannot_create(self, user_client, org_a):
        response = user_client.post(
            MAILBOXES_URL,
            {"address": "x@x.com", "provider": "ses"},
            format="json",
        )
        assert response.status_code == 403

    def test_unsupported_provider_returns_501(self, admin_client, org_a):
        # Mailgun isn't yet wired into the webhook, but the model accepts it.
        # Create a mailbox with provider=mailgun and verify the webhook 501s.
        mailbox = _make_mailbox(org_a, provider="mailgun")
        response = admin_client.post(
            f"/api/cases/inbound/{mailbox.id}/",
            {"Type": "Notification", "Message": "x", "Signature": "x", "SigningCertURL": "x", "SignatureVersion": "1"},
            format="json",
        )
        assert response.status_code == 501

    def test_inactive_mailbox_404(self, admin_client, org_a):
        mailbox = _make_mailbox(org_a, is_active=False)
        response = admin_client.post(
            f"/api/cases/inbound/{mailbox.id}/",
            {"Type": "Notification"},
            format="json",
        )
        assert response.status_code == 404

    def test_cross_org_isolation(self, admin_client, org_a, org_b):
        _make_mailbox(org_b, address="other@beta.com")
        response = admin_client.get(MAILBOXES_URL)
        assert response.json()["mailboxes"] == []


# ---------------------------------------------------------------------------
# Webhook (verification path bypassed via patch)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestWebhook:
    def test_subscription_confirmation_calls_subscribe(self, admin_client, org_a):
        mailbox = _make_mailbox(org_a)
        with (
            patch("cases.inbound_views.verify_sns_message") as verify,
            patch("cases.inbound_views.confirm_subscription") as confirm,
        ):
            verify.return_value = None
            confirm.return_value = None
            response = admin_client.post(
                f"/api/cases/inbound/{mailbox.id}/",
                {"Type": "SubscriptionConfirmation", "SubscribeURL": "https://x"},
                format="json",
            )
        assert response.status_code == 200
        assert confirm.called is True

    def test_notification_routes_through_pipeline(self, admin_client, org_a):
        mailbox = _make_mailbox(org_a)
        raw = _raw_email()
        with patch("cases.inbound_views.verify_sns_message") as verify:
            verify.return_value = None
            response = admin_client.post(
                f"/api/cases/inbound/{mailbox.id}/",
                {
                    "Type": "Notification",
                    "Message": raw,
                    "Signature": "x",
                    "SigningCertURL": "x",
                    "SignatureVersion": "1",
                },
                format="json",
            )
        assert response.status_code == 200, response.content
        body = response.json()
        assert body["created_case"] is True
        assert body["dropped"] is False

    def test_signature_failure_403(self, admin_client, org_a):
        from cases.inbound.sns import SNSVerificationError

        mailbox = _make_mailbox(org_a)
        with patch("cases.inbound_views.verify_sns_message") as verify:
            verify.side_effect = SNSVerificationError("nope")
            response = admin_client.post(
                f"/api/cases/inbound/{mailbox.id}/",
                {"Type": "Notification", "Message": "x", "Signature": "x", "SigningCertURL": "x", "SignatureVersion": "1"},
                format="json",
            )
        assert response.status_code == 403
