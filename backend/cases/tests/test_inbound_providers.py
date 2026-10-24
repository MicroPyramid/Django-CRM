"""Postmark and Mailgun deliveries to a mailbox's webhook.

Both post to the same `/api/cases/inbound/<mailbox id>/` URL as SES, and the
mailbox's `webhook_secret` is what proves a post came from the provider:
Postmark's basic-auth password, Mailgun's webhook signing key. A mailbox with
no secret accepts nothing.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from unittest.mock import patch
from urllib.parse import urlencode

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from cases import inbound_views
from cases.inbound.providers import (
    mailgun_signed,
    parse_mailgun,
    parse_postmark,
    postmark_authorized,
)
from cases.models import Case, EmailMessage, InboundMailbox
from common.models import Attachments
from conftest import rls_org
from leads.models import Lead

SECRET = "pm-secret-0123456789"
SIGNING_KEY = "key-mailgun-signing-0123456789"
REFUSED = {"error": True, "errors": "Signature verification failed"}
# Mailgun timestamps must be recent; every test runs within minutes of this.
NOW = str(int(time.time()))


@pytest.fixture
def anon():
    return APIClient()


def _mailbox(org, provider, *, creates="tickets", secret=SECRET, **extra):
    with rls_org(org):
        return InboundMailbox.objects.create(
            org=org,
            address=f"{provider}-{creates}@acme.test",
            provider=provider,
            webhook_secret=secret,
            creates=creates,
            is_active=True,
            **extra,
        )


def _url(mailbox):
    return f"/api/cases/inbound/{mailbox.id}/"


def _basic(user, password):
    return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()


# ---------------------------------------------------------------------------
# Postmark
# ---------------------------------------------------------------------------


def _postmark(**overrides):
    payload = {
        "From": "dana@example.com",
        "FromName": "Dana Smith",
        "FromFull": {"Email": "dana@example.com", "Name": "Dana Smith"},
        "To": "postmark-leads@acme.test",
        "ToFull": [{"Email": "postmark-leads@acme.test", "Name": ""}],
        "Cc": "",
        "CcFull": [],
        "OriginalRecipient": "postmark-leads@acme.test",
        "ReplyTo": "",
        "Subject": "Viewing request",
        "MessageID": "22c74902-a0c1-4511-804f-341342852c90",
        "Date": "Sat, 24 Oct 2026 10:00:00 +0000",
        "TextBody": "Can I view the flat? 555-222-3333",
        "HtmlBody": "<p>Can I view the flat?</p>",
        "Headers": [
            {"Name": "X-Spam-Status", "Value": "No"},
            {"Name": "Message-ID", "Value": "<CAG-1@mail.gmail.com>"},
        ],
        "Attachments": [
            {
                "Name": "floorplan.pdf",
                "Content": base64.b64encode(b"%PDF-1.4 plan").decode(),
                "ContentType": "application/pdf",
                "ContentLength": 13,
            }
        ],
    }
    payload.update(overrides)
    return payload


def _post_postmark(client, mailbox, payload, auth=_basic("postmark", SECRET)):
    extra = {"HTTP_AUTHORIZATION": auth} if auth is not None else {}
    return client.post(_url(mailbox), payload, format="json", **extra)


class TestPostmark:
    def test_a_good_password_opens_a_ticket(self, anon, org_a):
        mailbox = _mailbox(org_a, "postmark")
        payload = _postmark(To="postmark-tickets@acme.test")

        response = _post_postmark(anon, mailbox, payload)

        assert response.status_code == 200, response.content
        assert response.json()["created_case"] is True
        case = Case.objects.get(org=org_a)
        assert case.name == "Viewing request"
        row = EmailMessage.objects.get(org=org_a)
        assert row.message_id == "CAG-1@mail.gmail.com"
        assert row.from_address == "dana@example.com"

    def test_a_good_password_makes_a_lead_with_its_attachment(self, anon, org_a):
        org_a.default_country = "US"
        org_a.save(update_fields=["default_country"])
        mailbox = _mailbox(org_a, "postmark", creates="leads")

        response = _post_postmark(anon, mailbox, _postmark())

        assert response.status_code == 200, response.content
        assert response.json()["result"] == "created"
        lead = Lead.objects.get(org=org_a)
        assert lead.email == "dana@example.com"
        assert (lead.first_name, lead.last_name) == ("Dana", "Smith")
        assert lead.phone_e164 == "+15552223333"
        assert lead.external_id == "CAG-1@mail.gmail.com"
        files = Attachments.objects.filter(
            content_type=ContentType.objects.get_for_model(Lead), object_id=lead.id
        )
        assert list(files.values_list("file_name", flat=True)) == ["floorplan.pdf"]

    @pytest.mark.parametrize(
        "auth",
        [
            None,
            _basic("postmark", "wrong"),
            _basic("postmark", SECRET + "x"),
            "Basic not-base64!!",
            "Bearer " + SECRET,
            _basic("", ""),
        ],
    )
    def test_anything_but_the_password_is_refused(self, anon, org_a, auth):
        mailbox = _mailbox(org_a, "postmark", creates="leads")

        response = _post_postmark(anon, mailbox, _postmark(), auth=auth)

        assert response.status_code == 401
        assert response.json() == REFUSED
        assert not Lead.objects.filter(org=org_a).exists()
        assert not EmailMessage.objects.filter(org=org_a).exists()

    def test_a_mailbox_with_no_secret_accepts_nothing(self, anon, org_a):
        mailbox = _mailbox(org_a, "postmark", secret="")
        response = _post_postmark(anon, mailbox, _postmark(), auth=_basic("a", ""))
        assert response.status_code == 401

    def test_any_user_name_goes_with_the_password(self, anon, org_a):
        mailbox = _mailbox(org_a, "postmark", creates="leads")
        response = _post_postmark(
            anon, mailbox, _postmark(), auth=_basic("x:y", SECRET)
        )
        # Basic auth splits at the first colon, so "x" is the user name and
        # "y:<secret>" the password: refused.
        assert response.status_code == 401
        ok = _post_postmark(anon, mailbox, _postmark(), auth=_basic("", SECRET))
        assert ok.status_code == 200

    def test_a_retry_is_one_lead(self, anon, org_a):
        mailbox = _mailbox(org_a, "postmark", creates="leads")
        _post_postmark(anon, mailbox, _postmark())
        again = _post_postmark(anon, mailbox, _postmark())

        assert again.json()["reason"] == "already_received"
        assert Lead.objects.filter(org=org_a).count() == 1

    def test_spam_flagged_by_postmark_is_dropped_on_a_lead_address(self, anon, org_a):
        mailbox = _mailbox(org_a, "postmark", creates="leads")
        payload = _postmark(Headers=[{"Name": "X-Spam-Status", "Value": "Yes"}])

        response = _post_postmark(anon, mailbox, payload)

        assert response.json()["reason"] == "spam"
        assert not Lead.objects.filter(org=org_a).exists()

    def test_a_body_that_is_not_an_object_is_400(self, anon, org_a):
        mailbox = _mailbox(org_a, "postmark")
        response = _post_postmark(anon, mailbox, ["not", "an", "object"])
        assert response.status_code == 400

    def test_an_oversized_body_is_413_before_it_is_read(self, anon, org_a):
        mailbox = _mailbox(org_a, "postmark")
        response = anon.post(
            _url(mailbox),
            "{}",
            content_type="application/json",
            HTTP_AUTHORIZATION=_basic("postmark", SECRET),
            CONTENT_LENGTH=str(60 * 1024 * 1024),
        )
        assert response.status_code == 413


def test_parse_postmark_prefers_the_raw_email():
    raw = (
        "From: Raw Sender <raw@example.com>\r\n"
        "To: postmark-leads@acme.test\r\n"
        "Subject: From the raw source\r\n"
        "Message-ID: <raw-1@example.com>\r\n"
        "Reply-To: other@example.com\r\n"
        "\r\n"
        "Raw body.\r\n"
    )
    parsed = parse_postmark(_postmark(RawEmail=raw))
    assert parsed.from_address == "raw@example.com"
    assert parsed.message_id == "raw-1@example.com"
    assert parsed.raw_headers["Reply-To"] == "other@example.com"


def test_parse_postmark_fields():
    parsed = parse_postmark(
        _postmark(
            ReplyTo="Dana Home <home@example.com>",
            CcFull=[{"Email": "CC@Example.com", "Name": "C"}],
            Headers=[
                {"Name": "Auto-Submitted", "Value": "auto-generated"},
                {"Name": "Message-ID", "Value": "<CAG-1@mail.gmail.com>"},
            ],
        )
    )
    assert parsed.from_display_name == "Dana Smith"
    assert parsed.to_addresses == ["postmark-leads@acme.test"]
    assert parsed.cc_addresses == ["cc@example.com"]
    assert parsed.raw_headers["Reply-To"] == "Dana Home <home@example.com>"
    assert parsed.raw_headers["Auto-Submitted"] == "auto-generated"
    assert parsed.body_text.startswith("Can I view")
    assert parsed.attachments[0].payload == b"%PDF-1.4 plan"


def test_parse_postmark_falls_back_to_its_own_message_id():
    parsed = parse_postmark(_postmark(Headers=[]))
    assert parsed.message_id == "22c74902-a0c1-4511-804f-341342852c90@postmark"


def test_parse_postmark_skips_an_attachment_that_is_not_base64():
    parsed = parse_postmark(
        _postmark(Attachments=[{"Name": "x.pdf", "Content": "@@not base64@@"}])
    )
    assert parsed.attachments == []


def test_postmark_authorized_needs_a_secret():
    assert postmark_authorized(_basic("a", SECRET), SECRET) is True
    assert postmark_authorized(_basic("a", ""), "") is False
    assert postmark_authorized(None, SECRET) is False
    assert postmark_authorized(_basic("a", "é"), SECRET) is False


# ---------------------------------------------------------------------------
# Mailgun
# ---------------------------------------------------------------------------


def _signature(timestamp, token, key=SIGNING_KEY):
    return hmac.new(
        key.encode(), f"{timestamp}{token}".encode(), hashlib.sha256
    ).hexdigest()


def _mailgun(**overrides):
    timestamp, token = NOW, "t" * 50
    fields = {
        "timestamp": timestamp,
        "token": token,
        "signature": _signature(timestamp, token),
        "recipient": "mailgun-leads@acme.test",
        "sender": "bounce@example.com",
        "from": "Dana Smith <dana@example.com>",
        "subject": "Viewing request",
        "body-plain": "Can I view the flat? 555-222-3333",
        "body-html": "<p>Can I view the flat?</p>",
        "stripped-text": "Can I view the flat?",
        "message-headers": json.dumps(
            [
                ["From", "Dana Smith <dana@example.com>"],
                ["To", "mailgun-leads@acme.test"],
                ["Subject", "Viewing request"],
                ["Message-Id", "<mg-1@mail.example.com>"],
                ["Date", "Sat, 24 Oct 2026 10:00:00 +0000"],
            ]
        ),
    }
    fields.update(overrides)
    return fields


class TestMailgun:
    def test_a_good_signature_makes_a_lead_with_its_attachment(self, anon, org_a):
        org_a.default_country = "US"
        org_a.save(update_fields=["default_country"])
        mailbox = _mailbox(org_a, "mailgun", creates="leads", secret=SIGNING_KEY)
        fields = _mailgun(**{"attachment-count": "1"})
        fields["attachment-1"] = SimpleUploadedFile(
            "plan.pdf", b"%PDF plan", content_type="application/pdf"
        )

        response = anon.post(_url(mailbox), fields)  # multipart

        assert response.status_code == 200, response.content
        lead = Lead.objects.get(org=org_a)
        assert lead.email == "dana@example.com"
        assert lead.phone_e164 == "+15552223333"
        assert lead.external_id == "mg-1@mail.example.com"
        files = Attachments.objects.filter(
            content_type=ContentType.objects.get_for_model(Lead), object_id=lead.id
        )
        assert list(files.values_list("file_name", flat=True)) == ["plan.pdf"]

    def test_a_form_encoded_post_opens_a_ticket(self, anon, org_a):
        mailbox = _mailbox(org_a, "mailgun", secret=SIGNING_KEY)
        response = anon.post(
            _url(mailbox),
            urlencode(_mailgun()),
            content_type="application/x-www-form-urlencoded",
        )

        assert response.status_code == 200, response.content
        assert response.json()["created_case"] is True
        assert EmailMessage.objects.get(org=org_a).message_id == "mg-1@mail.example.com"

    @pytest.mark.parametrize(
        "change",
        [
            {"signature": "0" * 64},
            {"signature": _signature(NOW, "t" * 50, key="other-key")},
            {"timestamp": str(int(NOW) + 1)},
            {"token": "u" * 50},
            {"signature": ""},
        ],
    )
    def test_a_bad_signature_is_refused(self, anon, org_a, change):
        mailbox = _mailbox(org_a, "mailgun", creates="leads", secret=SIGNING_KEY)
        response = anon.post(_url(mailbox), _mailgun(**change))

        assert response.status_code == 401
        assert response.json() == REFUSED
        assert not Lead.objects.filter(org=org_a).exists()
        assert not EmailMessage.objects.filter(org=org_a).exists()

    def test_missing_signature_fields_are_refused(self, anon, org_a):
        mailbox = _mailbox(org_a, "mailgun", secret=SIGNING_KEY)
        fields = _mailgun()
        del fields["token"]
        assert anon.post(_url(mailbox), fields).status_code == 401

    def test_a_mailbox_with_no_signing_key_accepts_nothing(self, anon, org_a):
        mailbox = _mailbox(org_a, "mailgun", secret="")
        timestamp, token = NOW, "t"
        fields = _mailgun(
            timestamp=timestamp, token=token, signature=_signature(timestamp, token, "")
        )
        assert anon.post(_url(mailbox), fields).status_code == 401

    def test_a_subaccount_parent_signature_is_accepted(self, anon, org_a):
        mailbox = _mailbox(org_a, "mailgun", creates="leads", secret="parent-key")
        fields = _mailgun()
        fields["parent-signature"] = _signature(
            fields["timestamp"], fields["token"], "parent-key"
        )
        assert anon.post(_url(mailbox), fields).status_code == 200

    def test_spam_flagged_by_mailgun_is_dropped_on_a_lead_address(self, anon, org_a):
        mailbox = _mailbox(org_a, "mailgun", creates="leads", secret=SIGNING_KEY)
        headers = json.loads(_mailgun()["message-headers"])
        headers.append(["X-Mailgun-Sflag", "Yes"])
        response = anon.post(
            _url(mailbox), _mailgun(**{"message-headers": json.dumps(headers)})
        )
        assert response.json()["reason"] == "spam"


class TestMailgunReplay:
    """The signature covers only `timestamp` and `token`, so a captured post
    must not be accepted again: the timestamp must be recent, and a token
    delivers once per mailbox."""

    @staticmethod
    def _signed_at(offset, token="r" * 50):
        timestamp = str(int(time.time()) + offset)
        return _mailgun(
            timestamp=timestamp, token=token, signature=_signature(timestamp, token)
        )

    @pytest.mark.parametrize("offset", [-(8 * 3600 + 6 * 60), 6 * 60, -(10**9)])
    def test_a_stale_or_future_timestamp_is_refused(self, anon, org_a, offset):
        mailbox = _mailbox(org_a, "mailgun", creates="leads", secret=SIGNING_KEY)
        response = anon.post(_url(mailbox), self._signed_at(offset))

        assert response.status_code == 401
        assert response.json() == REFUSED
        assert not Lead.objects.filter(org=org_a).exists()

    @pytest.mark.parametrize("offset", [-8 * 3600, 4 * 60])
    def test_a_timestamp_inside_the_window_is_accepted(self, anon, org_a, offset):
        mailbox = _mailbox(org_a, "mailgun", creates="leads", secret=SIGNING_KEY)
        assert anon.post(_url(mailbox), self._signed_at(offset)).status_code == 200

    def test_a_reused_token_is_refused(self, anon, org_a):
        mailbox = _mailbox(org_a, "mailgun", creates="leads", secret=SIGNING_KEY)
        fields = self._signed_at(0)
        first = anon.post(_url(mailbox), fields)
        headers = json.loads(fields["message-headers"])
        headers[3] = ["Message-Id", "<another@mail.example.com>"]
        fields["message-headers"] = json.dumps(headers)
        replay = anon.post(_url(mailbox), fields)

        assert first.status_code == 200
        assert replay.status_code == 401
        assert replay.json() == REFUSED
        assert Lead.objects.filter(org=org_a).count() == 1

    def test_a_replay_while_the_first_post_is_delivering_is_refused(self, anon, org_a):
        mailbox = _mailbox(org_a, "mailgun", creates="leads", secret=SIGNING_KEY)
        fields = self._signed_at(0)
        replays = []
        deliver = inbound_views._deliver

        def deliver_and_replay(parsed, box, reading=None):
            if not replays:
                replays.append(None)
                replays[0] = APIClient().post(_url(mailbox), fields).status_code
            return deliver(parsed, box, reading)

        with patch.object(inbound_views, "_deliver", side_effect=deliver_and_replay):
            first = anon.post(_url(mailbox), fields)

        assert first.status_code == 200
        assert replays == [401]
        assert Lead.objects.filter(org=org_a).count() == 1

    def test_a_failed_delivery_frees_the_token_for_mailguns_retry(self, org_a):
        mailbox = _mailbox(org_a, "mailgun", creates="leads", secret=SIGNING_KEY)
        fields = self._signed_at(0)
        client = APIClient(raise_request_exception=False)
        with patch.object(inbound_views, "_deliver", side_effect=RuntimeError("down")):
            assert client.post(_url(mailbox), fields).status_code == 500

        assert client.post(_url(mailbox), fields).status_code == 200
        assert client.post(_url(mailbox), fields).status_code == 401
        assert Lead.objects.filter(org=org_a).count() == 1

    def test_only_a_signed_post_claims_its_token(self, anon, org_a):
        mailbox = _mailbox(org_a, "mailgun", creates="leads", secret=SIGNING_KEY)
        fields = self._signed_at(0)
        forged = dict(fields, signature="0" * 64)

        assert anon.post(_url(mailbox), forged).status_code == 401
        assert anon.post(_url(mailbox), fields).status_code == 200

    def test_a_token_is_remembered_per_mailbox(self, anon, org_a):
        first = _mailbox(org_a, "mailgun", creates="leads", secret=SIGNING_KEY)
        with rls_org(org_a):
            second = InboundMailbox.objects.create(
                org=org_a,
                address="mailgun-two@acme.test",
                provider="mailgun",
                webhook_secret=SIGNING_KEY,
                is_active=True,
            )
        fields = self._signed_at(0)
        assert anon.post(_url(first), fields).status_code == 200
        assert anon.post(_url(second), fields).status_code == 200


def test_mailgun_signed_checks_the_timestamp_window():
    now = time.time()
    for offset, expected in ((0, True), (-8 * 3600, True), (-8 * 3600 - 301, False)):
        timestamp = str(int(now) + offset)
        fields = _mailgun(
            timestamp=timestamp, signature=_signature(timestamp, "t" * 50)
        )
        assert mailgun_signed(fields, SIGNING_KEY, now=now) is expected
    for timestamp in ("", "abc", " 123", "1_761_300_000", "9" * 13):
        fields = _mailgun(timestamp=timestamp)
        assert mailgun_signed(fields, SIGNING_KEY) is False


def test_parse_mailgun_reads_body_mime():
    raw = (
        "From: Mime Sender <mime@example.com>\r\n"
        "To: mailgun-leads@acme.test\r\n"
        "Subject: Raw MIME\r\n"
        "Message-ID: <mime-1@example.com>\r\n"
        "\r\n"
        "From the raw MIME.\r\n"
    )
    parsed = parse_mailgun({"body-mime": raw}, {})
    assert parsed.from_address == "mime@example.com"
    assert parsed.message_id == "mime-1@example.com"
    assert "raw MIME" in parsed.body_text


def test_parse_mailgun_survives_malformed_headers():
    parsed = parse_mailgun(_mailgun(**{"message-headers": "not json"}), {})
    assert parsed.from_address == "dana@example.com"
    assert parsed.message_id == ""
    assert parsed.subject == "Viewing request"


def test_mailgun_signed_rejects_non_string_and_missing_values():
    good = _mailgun()
    assert mailgun_signed(good, SIGNING_KEY) is True
    assert mailgun_signed({}, SIGNING_KEY) is False
    assert mailgun_signed(good, "") is False


def test_imap_still_answers_501(anon, org_a):
    mailbox = _mailbox(org_a, "imap")
    response = anon.post(_url(mailbox), {"x": "y"}, format="json")
    assert response.status_code == 501
