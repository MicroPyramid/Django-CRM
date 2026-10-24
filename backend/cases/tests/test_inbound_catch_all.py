"""The catch-all webhook for generated addresses (`INBOUND_EMAIL_DOMAIN`).

One SES receipt rule and one SNS topic serve every generated address, so the
webhook trusts a notification only when its SNS signature verifies and its
TopicArn is exactly `INBOUND_EMAIL_TOPIC_ARN`. Each recipient is then routed to
its own org's active generated mailbox; an unknown recipient is dropped and
logged. Every signature below is genuinely verified.
"""

from __future__ import annotations

import json
import logging
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from django.db import connection
from rest_framework.test import APIClient

from cases import inbound_views
from cases.inbound.generated import lookup_token
from cases.inbound.text import innermost_forward
from cases.models import Case, EmailMessage, InboundMailbox
from cases.tests.test_inbound_sns import _signed_payload
from cases.tests.test_inbound_topic_pin import _real_verification, _signed_confirmation
from common.models import Org, PortalAccessToken
from common.portal_tokens import register_portal_token
from common.testing import set_modules_off
from conftest import rls_org
from leads.models import Lead

URL = "/api/cases/inbound/email/"
DOMAIN = "in.example.test"
TOPIC = "arn:aws:sns:us-east-1:123456789012:bottlecrm-inbound"
OTHER_TOPIC = "arn:aws:sns:us-east-1:999999999999:attacker"
REFUSED = {"error": True, "errors": "Signature verification failed"}


@pytest.fixture
def anon():
    return APIClient()


@pytest.fixture(scope="module")
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(autouse=True)
def configured(settings):
    settings.INBOUND_EMAIL_DOMAIN = DOMAIN
    settings.INBOUND_EMAIL_TOPIC_ARN = TOPIC


def _generated(org, local, *, creates="leads", is_active=True):
    """A generated mailbox, made the way the API makes one."""
    with rls_org(org):
        return InboundMailbox.objects.create(
            org=org,
            address=f"{local}@{DOMAIN}",
            provider="ses",
            creates=creates,
            is_generated=True,
            is_active=is_active,
        )


def _raw(to, *, message_id="<m1@example.com>", from_="Dana <dana@example.com>"):
    return (
        f"From: {from_}\r\n"
        f"To: {to}\r\n"
        "Subject: Viewing request\r\n"
        "Date: Sat, 24 Oct 2026 10:00:00 +0000\r\n"
        f"Message-ID: {message_id}\r\n"
        "\r\n"
        "Can I view the flat?\r\n"
    )


def _ses(raw, recipients):
    return json.dumps(
        {
            "notificationType": "Received",
            "receipt": {"recipients": recipients},
            "content": raw,
        }
    )


def _send(client, key, message, *, topic=TOPIC):
    payload = _signed_payload(key, topic_arn=topic, Message=message)
    with _real_verification(key):
        return client.post(URL, payload, format="json")


class TestRouting:
    def test_two_recipients_reach_two_orgs(self, anon, org_a, org_b, signing_key):
        a = _generated(org_a, "acme-a1b2c3")
        b = _generated(org_b, "beta-d4e5f6", creates="tickets")
        message = _ses(_raw(f"{a.address}, {b.address}"), [a.address, b.address])

        response = _send(anon, signing_key, message)

        assert response.status_code == 200, response.content
        assert response.json() == {"ok": True, "delivered": 2, "failed": 0}
        with rls_org(org_a):
            lead = Lead.objects.get(org=org_a)
        assert lead.email == "dana@example.com"
        assert lead.external_source == f"email:{a.id}"
        with rls_org(org_b):
            assert Case.objects.filter(org=org_b).count() == 1
            assert not Lead.objects.filter(org=org_b).exists()
        assert not Case.objects.filter(org=org_a).exists()

    def test_recipients_match_ignoring_case(self, anon, org_a, signing_key):
        a = _generated(org_a, "acme-a1b2c3")
        message = _ses(_raw(a.address), [a.address.upper()])
        assert _send(anon, signing_key, message).json()["delivered"] == 1

    def test_an_unknown_recipient_is_dropped_and_logged(
        self, anon, org_a, signing_key, caplog
    ):
        message = _ses(_raw(f"nobody-zzzzzz@{DOMAIN}"), [f"nobody-zzzzzz@{DOMAIN}"])

        with caplog.at_level(logging.WARNING, logger="cases.inbound_views"):
            response = _send(anon, signing_key, message)

        assert response.status_code == 200
        assert response.json() == {"ok": True, "delivered": 0, "failed": 0}
        assert "unknown recipient" in caplog.text
        assert "nobody-zzzzzz" not in caplog.text
        assert not EmailMessage.objects.exists()

    def test_a_recipient_on_another_domain_is_ignored(self, anon, org_a, signing_key):
        a = _generated(org_a, "acme-a1b2c3")
        message = _ses(_raw("leads@acme.test"), ["leads@acme.test"])
        assert _send(anon, signing_key, message).json()["delivered"] == 0
        assert a.email_messages.count() == 0

    def test_a_typed_mailbox_is_never_routed(self, anon, org_a, signing_key):
        with rls_org(org_a):
            typed = InboundMailbox.objects.create(
                org=org_a, address=f"typed@{DOMAIN}", creates="leads", is_active=True
            )
        # Even with a lookup row naming it, only a generated mailbox is routed.
        register_portal_token(
            lookup_token(typed.address),
            org_a.id,
            PortalAccessToken.INBOUND_MAILBOX,
            typed.id,
        )
        message = _ses(_raw(typed.address), [typed.address])
        assert _send(anon, signing_key, message).json()["delivered"] == 0
        assert not Lead.objects.filter(org=org_a).exists()

    def test_an_inactive_generated_mailbox_receives_nothing(
        self, anon, org_a, signing_key
    ):
        a = _generated(org_a, "acme-a1b2c3", is_active=False)
        message = _ses(_raw(a.address), [a.address])
        assert _send(anon, signing_key, message).json()["delivered"] == 0
        assert not Lead.objects.filter(org=org_a).exists()

    def test_a_mailbox_whose_module_is_off_receives_nothing(
        self, anon, org_a, signing_key
    ):
        a = _generated(org_a, "acme-a1b2c3")
        set_modules_off(org_a, "leads")
        message = _ses(_raw(a.address), [a.address])

        assert _send(anon, signing_key, message).json()["delivered"] == 0
        assert not EmailMessage.objects.filter(org=org_a).exists()

    def test_a_lookup_row_naming_another_org_finds_nothing(
        self, anon, org_a, org_b, signing_key
    ):
        a = _generated(org_a, "acme-a1b2c3")
        PortalAccessToken.objects.filter(resource_id=a.id).update(org=org_b)
        message = _ses(_raw(a.address), [a.address])

        assert _send(anon, signing_key, message).json()["delivered"] == 0
        assert not Lead.objects.exists()

    def test_a_raw_message_falls_back_to_its_headers(self, anon, org_a, signing_key):
        a = _generated(org_a, "acme-a1b2c3")
        response = _send(anon, signing_key, _raw(a.address))
        assert response.json()["delivered"] == 1

    def test_a_redelivery_is_one_lead(self, anon, org_a, signing_key):
        a = _generated(org_a, "acme-a1b2c3")
        message = _ses(_raw(a.address), [a.address])
        _send(anon, signing_key, message)
        _send(anon, signing_key, message)
        assert Lead.objects.filter(org=org_a).count() == 1


class TestOneRecipientFailing:
    def test_a_failure_in_one_org_never_blocks_another(
        self, anon, org_a, org_b, signing_key, caplog
    ):
        a = _generated(org_a, "acme-a1b2c3")
        b = _generated(org_b, "beta-d4e5f6")
        message = _ses(_raw(f"{a.address}, {b.address}"), [a.address, b.address])
        real = inbound_views._deliver

        def failing_for_a(parsed, mailbox, reading=None):
            if mailbox.id == a.id:
                raise RuntimeError("database went away")
            return real(parsed, mailbox, reading)

        with (
            patch("cases.inbound_views._deliver", side_effect=failing_for_a),
            caplog.at_level(logging.ERROR, logger="cases.inbound_views"),
        ):
            response = _send(anon, signing_key, message)

        # 500, so SNS delivers the notification again for the failed org.
        assert response.status_code == 500
        assert response.json() == {"ok": False, "delivered": 1, "failed": 1}
        assert "Catch-all delivery failed" in caplog.text
        assert a.address not in caplog.text
        assert Lead.objects.filter(org=org_b).count() == 1
        assert not Lead.objects.filter(org=org_a).exists()

        again = _send(anon, signing_key, message)
        assert again.status_code == 200
        assert again.json() == {"ok": True, "delivered": 2, "failed": 0}
        assert Lead.objects.filter(org=org_a).count() == 1
        assert Lead.objects.filter(org=org_b).count() == 1

    def test_the_email_is_read_once_for_every_recipient(
        self, anon, org_a, org_b, signing_key
    ):
        a = _generated(org_a, "acme-a1b2c3")
        b = _generated(org_b, "beta-d4e5f6")
        message = _ses(_raw(f"{a.address}, {b.address}"), [a.address, b.address])

        with patch(
            "cases.inbound.leads.innermost_forward", wraps=innermost_forward
        ) as reads:
            response = _send(anon, signing_key, message)

        assert response.json()["delivered"] == 2
        assert reads.call_count == 1


class TestTrust:
    def test_another_topic_is_refused(self, anon, org_a, signing_key):
        a = _generated(org_a, "acme-a1b2c3")
        message = _ses(_raw(a.address), [a.address])

        response = _send(anon, signing_key, message, topic=OTHER_TOPIC)

        assert response.status_code == 403
        assert response.json() == REFUSED
        assert not Lead.objects.exists()

    def test_a_tampered_message_is_refused(self, anon, org_a, signing_key):
        a = _generated(org_a, "acme-a1b2c3")
        payload = _signed_payload(
            signing_key, topic_arn=TOPIC, Message=_ses(_raw(a.address), [a.address])
        )
        payload["Message"] = _ses(_raw(a.address, from_="ceo@acme.test"), [a.address])
        with _real_verification(signing_key):
            response = anon.post(URL, payload, format="json")

        assert response.status_code == 403
        assert not Lead.objects.exists()

    def test_the_configured_topic_confirms_its_subscription(self, anon, signing_key):
        with (
            _real_verification(signing_key),
            patch("cases.inbound_views.confirm_subscription") as confirm,
        ):
            response = anon.post(
                URL, _signed_confirmation(signing_key, TOPIC), format="json"
            )
        assert response.status_code == 200
        assert response.json() == {"ok": True, "subscribed": True}
        assert confirm.called

    def test_another_topics_confirmation_is_never_fetched(self, anon, signing_key):
        with (
            _real_verification(signing_key),
            patch("cases.inbound_views.confirm_subscription") as confirm,
        ):
            response = anon.post(
                URL, _signed_confirmation(signing_key, OTHER_TOPIC), format="json"
            )
        assert response.status_code == 403
        assert not confirm.called

    @pytest.mark.parametrize("domain,topic", [("", TOPIC), (DOMAIN, ""), ("", "")])
    def test_unconfigured_answers_404(self, anon, signing_key, settings, domain, topic):
        settings.INBOUND_EMAIL_DOMAIN = domain
        settings.INBOUND_EMAIL_TOPIC_ARN = topic
        message = _ses(_raw(f"x@{DOMAIN}"), [f"x@{DOMAIN}"])
        assert _send(anon, signing_key, message).status_code == 404

    def test_snss_default_text_plain_body_is_read(self, anon, org_a, signing_key):
        """SNS posts `text/plain; charset=UTF-8` unless told otherwise."""
        a = _generated(org_a, "acme-a1b2c3")
        payload = _signed_payload(
            signing_key, topic_arn=TOPIC, Message=_ses(_raw(a.address), [a.address])
        )
        with _real_verification(signing_key):
            response = anon.post(
                URL,
                json.dumps(payload),
                content_type="text/plain; charset=UTF-8",
            )
        assert response.status_code == 200, response.content
        assert response.json()["delivered"] == 1

    def test_a_body_that_is_not_json_is_400(self, anon):
        response = anon.post(URL, "not json", content_type="application/json")
        assert response.status_code == 400

    def test_needs_no_signed_in_org(self, anon, org_a, signing_key):
        """SNS has no credential: the route must not ask for an org claim."""
        a = _generated(org_a, "acme-a1b2c3")
        response = _send(anon, signing_key, _ses(_raw(a.address), [a.address]))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Under a role RLS binds (CI's non-superuser run)
# ---------------------------------------------------------------------------


def _context(value):
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.current_org', %s, false)", [value])


@pytest.mark.postgres_only
def test_the_catch_all_reaches_two_orgs_under_enforced_rls(anon, signing_key):
    if connection.vendor != "postgresql":
        pytest.skip("RLS requires PostgreSQL")
    made = []
    for name, local in (("RLS One", "one-a1b2c3"), ("RLS Two", "two-d4e5f6")):
        org = Org.objects.create(name=name)
        _context(str(org.id))
        try:
            made.append((org, _generated(org, local)))
        finally:
            _context("")
    assert not InboundMailbox.objects.filter(is_generated=True).exists(), (
        "The empty context exposed inbound_mailbox: this role bypasses RLS."
    )
    addresses = [mailbox.address for _, mailbox in made]

    response = _send(anon, signing_key, _ses(_raw(", ".join(addresses)), addresses))

    assert response.status_code == 200, response.content
    assert response.json()["delivered"] == 2
    for org, mailbox in made:
        _context(str(org.id))
        try:
            assert Lead.objects.get(org=org).external_source == f"email:{mailbox.id}"
        finally:
            _context("")
