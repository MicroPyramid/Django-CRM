"""The lead address: email to a `creates=leads` mailbox becomes a lead.

Who the enquirer is decides everything here, so most tests read one email and
check which person the lead names. A portal's automated sender is never the
lead, a member is never the lead, and an email with nothing to go on still
makes a lead, flagged, rather than one shared lead for every such email.
"""

from __future__ import annotations

import json
import time
from datetime import timedelta
from email.message import EmailMessage as StdlibEmailMessage
from unittest.mock import patch

import phonenumbers
import pytest
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from cases.inbound import leads as inbound_leads
from cases.inbound.leads import (
    NO_CONTACT_NOTE,
    ingest_lead,
    lead_from_email,
    read_email,
)
from cases.inbound.parser import parse_raw_email
from cases.inbound.pipeline import ingest
from cases.inbound.text import innermost_forward
from cases.models import Case, EmailMessage, InboundMailbox
from cases.tests.test_inbound_email import SNS_TOPIC, _notification
from common.models import Attachments, Comment, PortalAccessToken, Profile, User
from common.portal_tokens import portal_token_hash
from common.testing import set_modules_off
from conftest import rls_org
from leads.models import Lead, LeadSource

ADDRESS = "leads@acme.test"
MAILBOXES_URL = "/api/cases/mailboxes/"


def _raw(
    *,
    from_="Zillow <noreply@zillow.com>",
    to=ADDRESS,
    subject="New contact for 12 Main St",
    body="",
    message_id="<z1@mail.zillow.com>",
    headers=(),
    html=None,
):
    lines = [
        f"From: {from_}",
        f"To: {to}",
        f"Subject: {subject}",
        "Date: Sat, 24 Oct 2026 10:00:00 +0000",
    ]
    if message_id:
        lines.append(f"Message-ID: {message_id}")
    lines += list(headers)
    lines.append("MIME-Version: 1.0")
    if html is not None:
        lines.append('Content-Type: text/html; charset="utf-8"')
        return "\r\n".join(lines) + "\r\n\r\n" + html
    lines.append('Content-Type: text/plain; charset="utf-8"')
    return "\r\n".join(lines) + "\r\n\r\n" + body


ZILLOW_BODY = (
    "You have a new lead from Zillow.\r\n"
    "\r\n"
    "Name: Maria Lopez\r\n"
    "Email: maria.lopez@example.com\r\n"
    "Phone: (555) 123-4567\r\n"
    "Message: I would like to see 12 Main St this weekend.\r\n"
    "\r\n"
    "Questions? Write to support@zillow.com or call 1-800-492-3863.\r\n"
)


@pytest.fixture
def us_org(org_a):
    org_a.default_country = "US"
    org_a.save(update_fields=["default_country"])
    return org_a


@pytest.fixture
def mailbox(us_org, user_profile):
    with rls_org(us_org):
        return InboundMailbox.objects.create(
            org=us_org,
            address=ADDRESS,
            provider="ses",
            topic_arn=SNS_TOPIC,
            creates=InboundMailbox.CREATES_LEADS,
            lead_source="email",
            lead_source_detail="Lead address",
            default_assignee=user_profile,
            is_active=True,
        )


def _ingest(mailbox, raw):
    return ingest_lead(parse_raw_email(raw), mailbox)


def _comments(record):
    return list(
        Comment.objects.filter(
            content_type=ContentType.objects.get_for_model(type(record)),
            object_id=record.id,
        ).values_list("comment", flat=True)
    )


# ---------------------------------------------------------------------------
# Who the enquirer is
# ---------------------------------------------------------------------------


class TestAutomatedSenders:
    def test_a_portal_notification_makes_a_lead_from_the_body(
        self, mailbox, us_org, user_profile
    ):
        outcome = _ingest(mailbox, _raw(body=ZILLOW_BODY))

        assert outcome.result == "created"
        lead = Lead.objects.get(org=us_org)
        assert lead.email == "maria.lopez@example.com"
        assert (lead.first_name, lead.last_name) == ("Maria", "Lopez")
        assert lead.phone_e164 == "+15551234567"
        assert lead.source == "email"
        assert lead.source_detail == "zillow.com"
        assert lead.title == "New contact for 12 Main St"
        assert lead.external_source == f"email:{mailbox.id}"
        assert lead.external_id == "z1@mail.zillow.com"
        assert "12 Main St this weekend" in lead.description
        assert list(lead.assigned_to.all()) == [user_profile]

    def test_the_sender_is_never_the_lead(self, mailbox, us_org):
        _ingest(mailbox, _raw(body=ZILLOW_BODY))
        assert not Lead.objects.filter(org=us_org, email__icontains="zillow").exists()

    def test_a_reply_to_on_a_portal_notification_is_the_enquirer(self, mailbox, us_org):
        raw = _raw(
            from_="Portal <no-reply@portal.example>",
            headers=["Reply-To: Jo Bloggs <jo@example.com>"],
            body="Someone asked about your listing.",
        )
        _ingest(mailbox, raw)

        lead = Lead.objects.get(org=us_org)
        assert lead.email == "jo@example.com"
        assert (lead.first_name, lead.last_name) == ("Jo", "Bloggs")
        assert lead.source_detail == "portal.example"

    @pytest.mark.parametrize(
        "headers",
        [
            ["Auto-Submitted: auto-generated"],
            ["Precedence: bulk"],
        ],
    )
    def test_machine_mail_from_a_person_like_address_reads_the_body(
        self, mailbox, us_org, headers
    ):
        raw = _raw(
            from_="Listings <listings@portal.example>",
            headers=headers,
            body="Enquiry from sam@example.com about unit 4.",
        )
        _ingest(mailbox, raw)

        lead = Lead.objects.get(org=us_org)
        assert lead.email == "sam@example.com"
        assert lead.source_detail == "portal.example"

    @pytest.mark.parametrize(
        "local",
        [
            "noreply",
            "no-reply",
            "donotreply",
            "do-not-reply",
            "notifications",
            "notification",
            "alerts",
            "mailer",
        ],
    )
    def test_every_automated_local_part(self, mailbox, us_org, local):
        raw = _raw(from_=f"{local}@portal.example", body="Contact: ann@example.com")
        _ingest(mailbox, raw)
        assert Lead.objects.get(org=us_org).email == "ann@example.com"

    def test_body_addresses_skip_everything_that_is_not_the_enquirer(
        self, mailbox, us_org, admin_profile
    ):
        body = (
            f"Sent to {ADDRESS} by noreply@another.example\r\n"
            "Agent: admin@test.com\r\n"
            "Portal help: help@zillow.com\r\n"
            "Enquirer: real.person@example.com\r\n"
        )
        _ingest(mailbox, _raw(body=body))
        assert Lead.objects.get(org=us_org).email == "real.person@example.com"

    def test_review_focus_5_no_reply_no_address_makes_separate_leads(
        self, mailbox, us_org
    ):
        """No Reply-To and no address in the body: a lead with no email each
        time, never one shared "noreply" lead that every portal email merges
        into."""
        for n in (1, 2):
            raw = _raw(
                message_id=f"<view-{n}@portal.example>",
                from_="noreply@portal.example",
                body="Someone viewed your listing at 12 Main St.",
            )
            assert _ingest(mailbox, raw).result == "created"

        leads = list(Lead.objects.filter(org=us_org))
        assert len(leads) == 2
        assert all(lead.email is None for lead in leads)
        assert all(lead.description.startswith(NO_CONTACT_NOTE) for lead in leads)

    def test_an_html_only_notification_is_read(self, mailbox, us_org):
        html = (
            "<html><head><style>p{color:red}</style></head><body>"
            "<p>Name: <b>Ravi Kumar</b></p>"
            '<p><a href="mailto:ravi@example.com">Email Ravi</a></p>'
            "<p>Phone: 555&#8209;987&#8209;6543</p>"
            "<script>var x = 'evil@example.com';</script>"
            "</body></html>"
        )
        _ingest(mailbox, _raw(html=html))

        lead = Lead.objects.get(org=us_org)
        assert lead.email == "ravi@example.com"
        assert (lead.first_name, lead.last_name) == ("Ravi", "Kumar")
        assert "color:red" not in lead.description
        assert "evil@example.com" not in lead.description


class TestPeople:
    def test_a_persons_email_is_the_lead(self, mailbox, us_org):
        raw = _raw(
            from_="Dana Smith <dana@example.com>",
            body="Hello, do you have anything in town?\r\nCall me: 555-222-3333",
        )
        _ingest(mailbox, raw)

        lead = Lead.objects.get(org=us_org)
        assert lead.email == "dana@example.com"
        assert (lead.first_name, lead.last_name) == ("Dana", "Smith")
        assert lead.phone_e164 == "+15552223333"
        # A person's mail keeps the mailbox's own sub-source.
        assert lead.source_detail == "Lead address"

    def test_reply_to_wins_when_it_differs_from_from(self, mailbox, us_org):
        raw = _raw(
            from_="Dana Smith <dana@example.com>",
            headers=["Reply-To: Dana at home <dana.home@example.com>"],
            body="Please answer at home.",
        )
        _ingest(mailbox, raw)

        lead = Lead.objects.get(org=us_org)
        assert lead.email == "dana.home@example.com"
        assert lead.first_name == "Dana"

    def test_a_members_own_email_is_dropped(self, mailbox, us_org, admin_profile):
        raw = _raw(from_="Admin <ADMIN@test.com>", body="Testing the lead address.")
        outcome = _ingest(mailbox, raw)

        assert outcome.dropped is True
        assert outcome.drop_reason == "member_sender"
        assert not Lead.objects.filter(org=us_org).exists()
        row = EmailMessage.objects.get(org=us_org)
        assert row.drop_reason == "member_sender"
        assert row.case_id is None

    def test_a_deactivated_members_email_is_dropped_too(self, mailbox, us_org):
        user = User.objects.create_user(email="gone@acme.test", password="x")
        Profile.objects.create(user=user, org=us_org, role="USER", is_active=False)

        outcome = _ingest(mailbox, _raw(from_="gone@acme.test", body="hi"))
        assert outcome.drop_reason == "member_sender"

    def test_a_member_of_another_org_is_an_ordinary_sender(
        self, mailbox, us_org, profile_b
    ):
        outcome = _ingest(mailbox, _raw(from_="userb@test.com", body="Interested."))
        assert outcome.result == "created"
        assert Lead.objects.get(org=us_org).email == "userb@test.com"

    def test_a_reply_to_naming_a_member_is_dropped(
        self, mailbox, us_org, admin_profile
    ):
        raw = _raw(
            from_="dana@example.com",
            headers=["Reply-To: admin@test.com"],
            body="x",
        )
        assert _ingest(mailbox, raw).drop_reason == "member_sender"


GMAIL_FORWARD = (
    "FYI, new enquiry below.\r\n"
    "\r\n"
    "---------- Forwarded message ---------\r\n"
    "From: Jane Doe <jane@example.com>\r\n"
    "Date: Mon, Oct 20, 2026 at 10:00 AM\r\n"
    "Subject: Interested in 12 Main St\r\n"
    "To: <admin@test.com>\r\n"
    "\r\n"
    "Hi, can I view 12 Main St on Saturday? My number is 555-444-1212.\r\n"
)

APPLE_FORWARD = (
    "Begin forwarded message:\r\n"
    "\r\n"
    "From: Jane Doe <jane@example.com>\r\n"
    "Subject: Interested in 12 Main St\r\n"
    "Date: 20 October 2026 at 10:00:00 BST\r\n"
    "To: admin@test.com\r\n"
    "\r\n"
    "Hi, can I view 12 Main St on Saturday? My number is 555-444-1212.\r\n"
)

OUTLOOK_FORWARD = (
    "\r\n"
    "________________________________\r\n"
    "From: Jane Doe [mailto:jane@example.com]\r\n"
    "Sent: Monday, October 20, 2026 10:00 AM\r\n"
    "To: Admin <admin@test.com>\r\n"
    "Subject: Interested in 12 Main St\r\n"
    "\r\n"
    "Hi, can I view 12 Main St on Saturday? My number is 555-444-1212.\r\n"
)


class TestForwarded:
    @pytest.mark.parametrize(
        "subject,body",
        [
            ("Fwd: Interested in 12 Main St", GMAIL_FORWARD),
            ("Fwd: Interested in 12 Main St", APPLE_FORWARD),
            ("FW: Interested in 12 Main St", OUTLOOK_FORWARD),
        ],
    )
    def test_a_hand_forwarded_email_uses_the_original_sender(
        self, mailbox, us_org, admin_profile, subject, body
    ):
        raw = _raw(from_="Admin <admin@test.com>", subject=subject, body=body)
        outcome = _ingest(mailbox, raw)

        assert outcome.result == "created", outcome
        lead = Lead.objects.get(org=us_org)
        assert lead.email == "jane@example.com"
        assert (lead.first_name, lead.last_name) == ("Jane", "Doe")
        assert lead.phone_e164 == "+15554441212"
        assert lead.title == "Interested in 12 Main St"
        assert "view 12 Main St on Saturday" in lead.description
        assert "FYI" not in lead.description
        assert lead.source_detail == "Lead address"

    def test_a_forwarded_portal_notification_reads_its_body(
        self, mailbox, us_org, admin_profile
    ):
        body = (
            "---------- Forwarded message ---------\r\n"
            "From: Zillow <noreply@zillow.com>\r\n"
            "Subject: New contact for 12 Main St\r\n"
            "\r\n" + ZILLOW_BODY
        )
        raw = _raw(from_="admin@test.com", subject="Fwd: New contact", body=body)
        _ingest(mailbox, raw)

        lead = Lead.objects.get(org=us_org)
        assert lead.email == "maria.lopez@example.com"
        assert lead.source_detail == "zillow.com"

    def test_a_forward_of_a_forward_reaches_the_original(
        self, mailbox, us_org, admin_profile, user_profile
    ):
        inner = GMAIL_FORWARD.replace("FYI, new enquiry below.", "Passing on.")
        body = (
            "---------- Forwarded message ---------\r\n"
            "From: Colleague <user@test.com>\r\n"
            "Subject: Fwd: Interested in 12 Main St\r\n"
            "\r\n" + inner
        )
        _ingest(mailbox, _raw(from_="admin@test.com", subject="Fwd: x", body=body))
        assert Lead.objects.get(org=us_org).email == "jane@example.com"

    def test_a_forwarded_members_email_is_dropped(self, mailbox, us_org, admin_profile):
        body = (
            "---------- Forwarded message ---------\r\n"
            "From: Colleague <user@test.com>\r\n"
            "Subject: note\r\n"
            "\r\n"
            "Internal note.\r\n"
        )
        raw = _raw(from_="admin@test.com", subject="Fwd: note", body=body)
        assert _ingest(mailbox, raw).drop_reason == "member_sender"


# ---------------------------------------------------------------------------
# Phone, body, attachments
# ---------------------------------------------------------------------------


class TestDetails:
    def test_a_labelled_phone_wins_and_a_toll_free_number_is_never_taken(
        self, mailbox, us_org
    ):
        body = (
            "Call us free on 1-800-492-3863, ref 2125550123.\r\n"
            "Mobile: 555 765 4321\r\n"
        )
        _ingest(mailbox, _raw(body=body + "Email: kim@example.com"))
        assert Lead.objects.get(org=us_org).phone_e164 == "+15557654321"

    def test_an_unlabelled_toll_free_number_is_skipped(self, mailbox, us_org):
        body = "Questions? 1-800-492-3863\r\nkim@example.com wrote 555 765 4321"
        _ingest(mailbox, _raw(body=body))
        assert Lead.objects.get(org=us_org).phone_e164 == "+15557654321"

    def test_a_local_number_in_an_org_with_no_country_is_not_a_phone(
        self, mailbox, us_org
    ):
        us_org.default_country = None
        us_org.save(update_fields=["default_country"])
        mailbox.refresh_from_db()

        _ingest(mailbox, _raw(body="Phone: 555-123-4567"))
        lead = Lead.objects.get(org=us_org)
        assert lead.phone_e164 == ""
        assert lead.description.startswith(NO_CONTACT_NOTE)

    def test_an_international_number_parses_without_a_country(self, mailbox, us_org):
        us_org.default_country = None
        us_org.save(update_fields=["default_country"])
        mailbox.refresh_from_db()

        _ingest(mailbox, _raw(body="Phone: +44 20 7946 0958"))
        assert Lead.objects.get(org=us_org).phone_e164 == "+442079460958"

    def test_no_email_matches_by_phone(self, mailbox, us_org):
        with rls_org(us_org):
            existing = Lead.objects.create(
                org=us_org, first_name="Old", phone="+1 555 123 4567", status="assigned"
            )
        raw = _raw(from_="noreply@portal.example", body="Callback: (555) 123-4567")
        outcome = _ingest(mailbox, raw)

        assert outcome.result == "merged"
        assert outcome.lead.id == existing.id

    def test_quoted_history_is_stripped(self, mailbox, us_org):
        body = (
            "Yes, Saturday works.\r\n"
            "\r\n"
            "On Mon, Oct 20, 2026 at 10:00 AM Agent <agent@acme.test> wrote:\r\n"
            "> Would Saturday suit you?\r\n"
            "> old-quote@example.com\r\n"
        )
        _ingest(mailbox, _raw(from_="dana@example.com", body=body))

        description = Lead.objects.get(org=us_org).description
        assert "Saturday works" in description
        assert "Would Saturday suit you" not in description

    def test_the_body_is_capped_at_20000_characters(self, mailbox, us_org):
        _ingest(mailbox, _raw(from_="dana@example.com", body="x" * 30_000))
        assert len(Lead.objects.get(org=us_org).description) == 20_000

    def test_the_subject_is_cut_to_the_title_column(self, mailbox, us_org):
        _ingest(mailbox, _raw(from_="dana@example.com", subject="s" * 400, body="hi"))
        assert len(Lead.objects.get(org=us_org).title) == 255

    def test_attachments_land_on_the_lead_and_oversized_ones_are_skipped(
        self, mailbox, us_org, monkeypatch
    ):
        monkeypatch.setattr("common.utils.ATTACHMENT_MAX_BYTES", 1000)
        msg = StdlibEmailMessage()
        msg["From"] = "Dana <dana@example.com>"
        msg["To"] = ADDRESS
        msg["Subject"] = "Plans attached"
        msg["Message-ID"] = "<att@example.com>"
        msg.set_content("See attached.")
        msg.add_attachment(b"%PDF small", maintype="application", subtype="pdf",
                           filename="../../plan.pdf")  # fmt: skip
        msg.add_attachment(b"x" * 2000, maintype="application", subtype="pdf",
                           filename="huge.pdf")  # fmt: skip

        ingest_lead(parse_raw_email(msg.as_bytes()), mailbox)

        lead = Lead.objects.get(org=us_org)
        files = Attachments.objects.filter(
            content_type=ContentType.objects.get_for_model(Lead), object_id=lead.id
        )
        assert list(files.values_list("file_name", flat=True)) == ["plan.pdf"]


class TestHostileBodies:
    """Bodies built to make the forward scanner rescan, or the phone matcher
    try every number: each must stay linear."""

    @pytest.mark.parametrize(
        "body",
        [
            "From: a\n" * (100_000 // 8),
            "---------- Forwarded message ---------\nFrom: a\n" * (100_000 // 47),
            "From: a\n" + "To: b\n" * (100_000 // 6),
            "Begin forwarded message:\n" + "\n" * 50_000 + "From: a\n" * 6_000,
            "phone " + "1234567 " * (100_000 // 8),
            ("phone " + "1234567 " * 60 + "\n") * (100_000 // 487),
            ("1234567 " * 60 + "\n") * (100_000 // 481),
            ("tel " + "12345 " * 80 + "\n") * (100_000 // 485),
        ],
        ids=[
            "from-lines",
            "forward-blocks",
            "header-run",
            "blank-gap",
            "one-line-of-numbers",
            "labelled-lines-of-numbers",
            "unlabelled-lines-of-numbers",
            "labelled-short-numbers",
        ],
    )
    def test_a_100_kb_adversarial_body_reads_in_under_a_second(self, body):
        parsed = parse_raw_email(
            _raw(from_="dana@example.com", subject="Fwd: x", body=body)
        )
        started = time.perf_counter()
        read_email(parsed).phone("US")
        assert time.perf_counter() - started < 1.0

    def test_a_number_past_the_first_200_lines_is_not_read(self):
        early = "Thanks\n" * 150 + "Phone: (555) 123-4567\n"
        late = "Thanks\n" * 250 + "Phone: (555) 123-4567\n"
        assert read_email(parse_raw_email(_raw(body=early))).phone("US")
        assert read_email(parse_raw_email(_raw(body=late))).phone("US") == ""

    def test_a_labelled_line_is_tried_once(self):
        body = "Phone: none given\nMessage: hello\nCall me\n"
        reading = read_email(parse_raw_email(_raw(body=body)))
        matcher = phonenumbers.PhoneNumberMatcher
        with patch.object(phonenumbers, "PhoneNumberMatcher", wraps=matcher) as tried:
            assert reading.phone("US") == ""
        assert [c.args[0] for c in tried.call_args_list] == [
            "Phone: none given",
            "Message: hello",
            "Call me",
        ]

    def test_the_labelled_number_still_wins_over_an_earlier_one(self):
        body = "Office 555-222-3333\nMobile: 555-444-5555\n"
        reading = read_email(parse_raw_email(_raw(body=body)))
        assert reading.phone("US") == "555-444-5555"

    def test_a_wrapped_header_still_finds_the_original(self):
        body = (
            "---------- Forwarded message ---------\n"
            "From: Jane Doe <jane@example.com>\n"
            "To: one@example.com, two@example.com,\n"
            " three@example.com\n"
            "Subject: Viewing\n"
            "\n"
            "Can I view it?\n"
        )
        found = innermost_forward(body, "Fwd: Viewing")
        assert (found.address, found.subject) == ("jane@example.com", "Viewing")
        assert found.body.strip() == "Can I view it?"

    def test_a_failed_block_does_not_hide_a_later_forward(self):
        body = (
            "---------- Forwarded message ---------\n"
            "From: nobody at all\n"
            "---------- Forwarded message ---------\n"
            "From: Jane Doe <jane@example.com>\n"
            "\n"
            "Hello\n"
        )
        assert innermost_forward(body, "Fwd: x").address == "jane@example.com"

    def test_an_over_long_header_value_is_cut(self):
        body = (
            "---------- Forwarded message ---------\n"
            "From: Jane <jane@example.com>\n"
            "Subject: " + "s" * 5000 + "\n"
            "\n"
            "Hello\n"
        )
        assert len(innermost_forward(body, "Fwd: x").subject) == 1000


# ---------------------------------------------------------------------------
# Drops, repeats and limits
# ---------------------------------------------------------------------------


class TestDropsAndRepeats:
    def test_the_same_message_id_twice_is_one_lead(self, mailbox, us_org):
        first = _ingest(mailbox, _raw(body=ZILLOW_BODY))
        again = _ingest(mailbox, _raw(body=ZILLOW_BODY))

        assert first.result == "created"
        assert again.dropped is True and again.drop_reason == "already_received"
        assert Lead.objects.filter(org=us_org).count() == 1
        assert _comments(first.lead) == []

    def test_a_repeat_delivery_of_a_merged_email_does_not_merge_twice(
        self, mailbox, us_org
    ):
        _ingest(mailbox, _raw(message_id="<a@x>", from_="dana@example.com", body="1"))
        merged = _ingest(
            mailbox, _raw(message_id="<b@x>", from_="dana@example.com", body="two")
        )
        again = _ingest(
            mailbox, _raw(message_id="<b@x>", from_="dana@example.com", body="two")
        )

        assert merged.result == "merged"
        assert again.drop_reason == "already_received"
        assert len(_comments(merged.lead)) == 1

    def test_the_same_email_to_two_lead_addresses_in_one_org_is_one_arrival(
        self, mailbox, us_org
    ):
        with rls_org(us_org):
            second = InboundMailbox.objects.create(
                org=us_org,
                address="agent2@acme.test",
                creates=InboundMailbox.CREATES_LEADS,
                is_active=True,
            )
        _ingest(mailbox, _raw(body=ZILLOW_BODY))
        outcome = _ingest(second, _raw(body=ZILLOW_BODY))

        assert outcome.drop_reason == "already_received"
        assert Lead.objects.filter(org=us_org).count() == 1

    def test_a_lead_email_does_not_hide_the_same_email_from_a_ticket_mailbox(
        self, mailbox, us_org
    ):
        with rls_org(us_org):
            support = InboundMailbox.objects.create(
                org=us_org, address="support@acme.test", is_active=True
            )
        raw = _raw(from_="dana@example.com", to=f"{ADDRESS}, support@acme.test")
        _ingest(mailbox, raw)
        result = ingest(parse_raw_email(raw), support)

        assert result.created_case is True
        assert Lead.objects.filter(org=us_org).count() == 1

    def test_the_501st_email_in_a_day_is_dropped(self, mailbox, us_org):
        with rls_org(us_org):
            EmailMessage.objects.bulk_create(
                EmailMessage(
                    org=us_org,
                    mailbox=mailbox,
                    message_id=f"lead:seed-{n}",
                    from_address="",
                    received_at=timezone.now(),
                )
                for n in range(inbound_leads.DAILY_LEAD_LIMIT)
            )
        rows = EmailMessage.objects.filter(org=us_org).count()
        outcome = _ingest(mailbox, _raw(body=ZILLOW_BODY))

        assert outcome.drop_reason == "daily_limit"
        assert not Lead.objects.filter(org=us_org).exists()
        # Past the cap nothing is written, so a flood adds no rows.
        assert EmailMessage.objects.filter(org=us_org).count() == rows

    def test_past_the_limit_the_body_is_never_read(
        self, mailbox, us_org, admin_profile, monkeypatch
    ):
        monkeypatch.setattr(inbound_leads, "DAILY_LEAD_LIMIT", 1)
        _ingest(mailbox, _raw(message_id="<first@x>", from_="p1@example.com"))
        rows = EmailMessage.objects.filter(org=us_org).count()
        parsed = parse_raw_email(_raw(message_id="<x@x>", body=ZILLOW_BODY))
        shared = read_email(parsed)
        with (
            patch.object(inbound_leads, "read_email") as reads,
            patch.object(inbound_leads, "_first_phone") as phones,
        ):
            assert ingest_lead(parsed, mailbox).drop_reason == "daily_limit"
            assert ingest_lead(parsed, mailbox, shared).drop_reason == "daily_limit"
            # A member's own mail past the cap is not recorded either.
            member = parse_raw_email(_raw(message_id="<m@x>", from_="admin@test.com"))
            assert ingest_lead(member, mailbox).drop_reason == "daily_limit"
        reads.assert_not_called()
        phones.assert_not_called()
        assert EmailMessage.objects.filter(org=us_org).count() == rows

    def test_an_email_over_one_addresss_limit_still_lands_at_another(
        self, mailbox, us_org, monkeypatch
    ):
        monkeypatch.setattr(inbound_leads, "DAILY_LEAD_LIMIT", 1)
        with rls_org(us_org):
            second = InboundMailbox.objects.create(
                org=us_org,
                address="agent2@acme.test",
                creates=InboundMailbox.CREATES_LEADS,
                is_active=True,
            )
        _ingest(mailbox, _raw(message_id="<first@x>", from_="p1@example.com"))
        raw = _raw(message_id="<both@x>", from_="p2@example.com")

        assert _ingest(mailbox, raw).drop_reason == "daily_limit"
        assert _ingest(second, raw).result == "created"

    def test_a_members_email_dropped_at_one_address_is_not_claimed_org_wide(
        self, mailbox, us_org, admin_profile
    ):
        with rls_org(us_org):
            second = InboundMailbox.objects.create(
                org=us_org,
                address="agent2@acme.test",
                creates=InboundMailbox.CREATES_LEADS,
                is_active=True,
            )
        raw = _raw(from_="admin@test.com", body="note")

        assert _ingest(mailbox, raw).drop_reason == "member_sender"
        # Judged again at the other address, not "already received".
        assert _ingest(second, raw).drop_reason == "member_sender"
        # A repeat at the same address is.
        assert _ingest(mailbox, raw).drop_reason == "already_received"
        assert EmailMessage.objects.filter(org=us_org).count() == 2

    def test_mail_from_another_of_the_orgs_addresses_is_dropped(self, mailbox, us_org):
        with rls_org(us_org):
            InboundMailbox.objects.create(org=us_org, address="support@acme.test")
        raw = _raw(from_="Support <support@acme.test>", body="dana@example.com")
        assert _ingest(mailbox, raw).drop_reason == "own_address"

    def test_yesterdays_emails_do_not_count_toward_the_limit(
        self, mailbox, us_org, monkeypatch
    ):
        monkeypatch.setattr(inbound_leads, "DAILY_LEAD_LIMIT", 2)
        for n in (1, 2):
            _ingest(mailbox, _raw(message_id=f"<{n}@x>", from_=f"p{n}@example.com"))
        assert _ingest(mailbox, _raw(message_id="<3@x>")).drop_reason == "daily_limit"

        EmailMessage.objects.filter(org=us_org).update(
            created_at=timezone.now() - timedelta(hours=25)
        )
        assert _ingest(mailbox, _raw(message_id="<4@x>")).result == "created"

    def test_drops_do_not_count_toward_the_limit(
        self, mailbox, us_org, admin_profile, monkeypatch
    ):
        monkeypatch.setattr(inbound_leads, "DAILY_LEAD_LIMIT", 1)
        _ingest(mailbox, _raw(message_id="<m@x>", from_="admin@test.com"))
        assert _ingest(mailbox, _raw(body=ZILLOW_BODY)).result == "created"

    def test_a_bounce_is_dropped(self, mailbox, us_org):
        raw = (
            "From: MAILER-DAEMON@example.com\r\n"
            f"To: {ADDRESS}\r\n"
            "Subject: Undeliverable\r\n"
            "Message-ID: <bounce@x>\r\n"
            "MIME-Version: 1.0\r\n"
            "Content-Type: multipart/report; report-type=delivery-status; "
            'boundary="b"\r\n\r\n--b\r\nContent-Type: text/plain\r\n\r\n'
            "maria@example.com failed.\r\n--b--\r\n"
        )
        assert _ingest(mailbox, raw).drop_reason == "bounce"
        assert not Lead.objects.filter(org=us_org).exists()

    def test_mail_from_the_address_itself_is_dropped(self, mailbox, us_org):
        raw = _raw(from_=f"Leads <{ADDRESS.upper()}>", body="dana@example.com")
        assert _ingest(mailbox, raw).drop_reason == "own_address"

    def test_lead_addresses_keep_auto_submitted_and_list_mail(self, mailbox, us_org):
        raw = _raw(
            headers=[
                "Auto-Submitted: auto-generated",
                "Precedence: bulk",
                "X-Autoreply: yes",
                "List-Id: <alerts.portal.example>",
                "List-Unsubscribe: <mailto:u@portal.example>",
            ],
            body=ZILLOW_BODY,
        )
        assert _ingest(mailbox, raw).result == "created"

    def test_a_missing_message_id_still_makes_one_lead_per_email(self, mailbox, us_org):
        raw = _raw(message_id="", from_="dana@example.com", body="Hello")
        first = _ingest(mailbox, raw)
        again = _ingest(mailbox, raw)

        assert first.result == "created"
        assert first.lead.external_id.startswith("sha256:")
        assert again.drop_reason == "already_received"


def test_lead_from_email_returns_none_only_for_a_member(mailbox, admin_profile):
    member = lead_from_email(
        parse_raw_email(_raw(from_="admin@test.com", body="x")), mailbox
    )
    stranger = lead_from_email(parse_raw_email(_raw(body=ZILLOW_BODY)), mailbox)
    assert member is None
    assert stranger.values["email"] == "maria.lopez@example.com"
    assert stranger.external_source == f"email:{mailbox.id}"
    assert stranger.channel_label == f"email to {ADDRESS}"


def test_a_ticket_mailbox_with_auto_submitted_still_drops(org_a):
    with rls_org(org_a):
        support = InboundMailbox.objects.create(
            org=org_a, address="support@acme.test", is_active=True
        )
    raw = _raw(
        from_="dana@example.com",
        to="support@acme.test",
        headers=["Auto-Submitted: auto-replied"],
    )
    result = ingest(parse_raw_email(raw), support)

    assert result.dropped is True and result.drop_reason == "auto_submitted"
    assert not Case.objects.filter(org=org_a).exists()
    assert not Lead.objects.filter(org=org_a).exists()


# ---------------------------------------------------------------------------
# Through the SES webhook, and the module rule
# ---------------------------------------------------------------------------


def _ses(raw, *, spam="PASS", virus="PASS", recipients=(ADDRESS,)):
    return json.dumps(
        {
            "notificationType": "Received",
            "receipt": {
                "recipients": list(recipients),
                "spamVerdict": {"status": spam},
                "virusVerdict": {"status": virus},
            },
            "content": raw,
        }
    )


def _webhook(client, mailbox, message):
    with patch("cases.inbound_views.verify_sns_message"):
        return client.post(
            f"/api/cases/inbound/{mailbox.id}/",
            _notification(SNS_TOPIC, message),
            format="json",
        )


class TestSesWebhook:
    def test_a_notification_makes_a_lead(self, mailbox, us_org, unauthenticated_client):
        response = _webhook(
            unauthenticated_client, mailbox, _ses(_raw(body=ZILLOW_BODY))
        )

        assert response.status_code == 200, response.content
        lead = Lead.objects.get(org=us_org)
        assert response.json() == {
            "ok": True,
            "lead_id": str(lead.id),
            "result": "created",
            "dropped": False,
            "reason": "",
        }
        assert not Case.objects.filter(org=us_org).exists()

    def test_snss_default_text_plain_body_is_read(
        self, mailbox, us_org, unauthenticated_client
    ):
        """SNS posts `text/plain; charset=UTF-8` unless the subscription's
        delivery policy says otherwise; that used to answer 415."""
        body = json.dumps(_notification(SNS_TOPIC, _ses(_raw(body=ZILLOW_BODY))))
        with patch("cases.inbound_views.verify_sns_message"):
            response = unauthenticated_client.post(
                f"/api/cases/inbound/{mailbox.id}/",
                body,
                content_type="text/plain; charset=UTF-8",
            )
        assert response.status_code == 200, response.content
        assert Lead.objects.filter(org=us_org).count() == 1

    @pytest.mark.parametrize(
        "verdicts,reason",
        [({"spam": "FAIL"}, "spam"), ({"virus": "FAIL"}, "virus")],
    )
    def test_ses_spam_and_virus_verdicts_are_dropped(
        self, mailbox, us_org, unauthenticated_client, verdicts, reason
    ):
        message = _ses(_raw(body=ZILLOW_BODY), **verdicts)
        response = _webhook(unauthenticated_client, mailbox, message)

        assert response.status_code == 200
        assert response.json()["reason"] == reason
        assert not Lead.objects.filter(org=us_org).exists()

    def test_a_gray_verdict_is_kept(self, mailbox, us_org, unauthenticated_client):
        message = _ses(_raw(body=ZILLOW_BODY), spam="GRAY")
        _webhook(unauthenticated_client, mailbox, message)
        assert Lead.objects.filter(org=us_org).count() == 1

    def test_a_ticket_mailbox_ignores_verdicts_as_before(
        self, us_org, unauthenticated_client
    ):
        with rls_org(us_org):
            support = InboundMailbox.objects.create(
                org=us_org,
                address="support@acme.test",
                topic_arn=SNS_TOPIC,
                is_active=True,
            )
        raw = _raw(from_="dana@example.com", to="support@acme.test")
        message = _ses(raw, spam="FAIL", recipients=["support@acme.test"])
        response = _webhook(unauthenticated_client, support, message)

        assert response.json()["created_case"] is True

    def test_a_ticket_mailbox_reads_a_text_plain_body_too(
        self, us_org, unauthenticated_client
    ):
        with rls_org(us_org):
            support = InboundMailbox.objects.create(
                org=us_org,
                address="support@acme.test",
                topic_arn=SNS_TOPIC,
                is_active=True,
            )
        raw = _raw(from_="dana@example.com", to="support@acme.test")
        message = _ses(raw, recipients=["support@acme.test"])
        with patch("cases.inbound_views.verify_sns_message"):
            response = unauthenticated_client.post(
                f"/api/cases/inbound/{support.id}/",
                json.dumps(_notification(SNS_TOPIC, message)),
                content_type="text/plain; charset=UTF-8",
            )
        assert response.status_code == 200, response.content
        assert response.json()["created_case"] is True

    def test_leads_off_answers_like_an_unknown_mailbox(
        self, mailbox, us_org, unauthenticated_client
    ):
        set_modules_off(us_org, "leads")
        response = _webhook(
            unauthenticated_client, mailbox, _ses(_raw(body=ZILLOW_BODY))
        )

        assert response.status_code == 404
        assert response.json() == {"error": True, "errors": "Mailbox not found"}
        assert not EmailMessage.objects.filter(org=us_org).exists()

    def test_tickets_off_does_not_stop_a_lead_address(
        self, mailbox, us_org, unauthenticated_client
    ):
        with rls_org(us_org):
            support = InboundMailbox.objects.create(
                org=us_org,
                address="support@acme.test",
                topic_arn=SNS_TOPIC,
                is_active=True,
            )
        set_modules_off(us_org, "tickets")

        lead_answer = _webhook(
            unauthenticated_client, mailbox, _ses(_raw(body=ZILLOW_BODY))
        )
        ticket_raw = _raw(from_="dana@example.com", to="support@acme.test")
        ticket_answer = _webhook(
            unauthenticated_client,
            support,
            _ses(ticket_raw, recipients=["support@acme.test"]),
        )

        assert lead_answer.status_code == 200
        assert Lead.objects.filter(org=us_org).count() == 1
        assert ticket_answer.status_code == 404
        assert not Case.objects.filter(org=us_org).exists()


# ---------------------------------------------------------------------------
# The mailbox API
# ---------------------------------------------------------------------------


def _create(client, **body):
    return client.post(MAILBOXES_URL, body, format="json")


class TestMailboxApi:
    def test_an_admin_creates_a_lead_address(self, admin_client, org_a):
        response = _create(
            admin_client,
            address="leads@acme.test",
            provider="ses",
            creates="leads",
            lead_source="google ads",
            lead_source_detail="Spring campaign",
        )

        assert response.status_code == 201, response.content
        data = response.json()
        assert data["creates"] == "leads"
        assert data["lead_source"] == "google ads"
        assert data["lead_source_detail"] == "Spring campaign"
        assert data["is_generated"] is False
        assert "generate_address" not in data

    def test_a_member_cannot_create_one(self, user_client, org_a):
        response = _create(user_client, address="l@acme.test", creates="leads")
        assert response.status_code == 403
        assert not InboundMailbox.objects.filter(org=org_a).exists()

    def test_creates_defaults_to_tickets(self, admin_client, org_a):
        data = _create(admin_client, address="s@acme.test").json()
        assert data["creates"] == "tickets"
        assert data["lead_source"] == "email"

    def test_an_unknown_creates_is_refused(self, admin_client, org_a):
        response = _create(admin_client, address="s@acme.test", creates="deals")
        assert response.status_code == 400
        assert "creates" in response.json()["errors"]

    def test_an_unknown_lead_source_is_refused(self, admin_client, org_a):
        response = _create(
            admin_client, address="s@acme.test", creates="leads", lead_source="nope"
        )
        assert response.status_code == 400
        assert "lead_source" in response.json()["errors"]

    def test_a_retired_source_cannot_be_chosen_but_a_stored_one_stays(
        self, admin_client, org_a
    ):
        LeadSource.objects.create(org=org_a, key="fair", label="Fair", is_active=False)
        refused = _create(
            admin_client, address="s@acme.test", creates="leads", lead_source="fair"
        )
        assert refused.status_code == 400

        with rls_org(org_a):
            mbx = InboundMailbox.objects.create(
                org=org_a, address="kept@acme.test", lead_source="fair"
            )
        kept = admin_client.put(
            f"{MAILBOXES_URL}{mbx.id}/",
            {"lead_source": "fair", "lead_source_detail": "x"},
            format="json",
        )
        assert kept.status_code == 200, kept.content

    def test_a_sub_source_over_100_characters_is_refused(self, admin_client, org_a):
        response = _create(
            admin_client,
            address="s@acme.test",
            creates="leads",
            lead_source_detail="d" * 101,
        )
        assert response.status_code == 400

    def test_a_lead_address_needs_leads_on(self, admin_client, org_a):
        set_modules_off(org_a, "leads")
        refused = _create(admin_client, address="l@acme.test", creates="leads")
        allowed = _create(admin_client, address="t@acme.test", creates="tickets")

        assert refused.status_code == 400
        assert refused.json()["errors"]["creates"] == [
            "Leads is switched off for this organization."
        ]
        assert allowed.status_code == 201

    def test_a_ticket_address_needs_tickets_on(self, admin_client, org_a):
        set_modules_off(org_a, "tickets")
        refused = _create(admin_client, address="t@acme.test", creates="tickets")
        allowed = _create(admin_client, address="l@acme.test", creates="leads")

        assert refused.status_code == 400
        assert allowed.status_code == 201

    def test_the_endpoints_work_with_tickets_off_and_leads_on(
        self, admin_client, user_client, org_a
    ):
        set_modules_off(org_a, "tickets")
        assert admin_client.get(MAILBOXES_URL).status_code == 200
        assert user_client.get(MAILBOXES_URL).status_code == 200

        set_modules_off(org_a, "tickets", "leads")
        response = admin_client.get(MAILBOXES_URL)
        assert response.status_code == 404
        assert response.json()["code"] == "module_off"

    def test_a_mailbox_cannot_be_switched_on_while_its_module_is_off(
        self, admin_client, org_a
    ):
        with rls_org(org_a):
            leads_box = InboundMailbox.objects.create(
                org=org_a, address="l@acme.test", creates="leads", is_active=False
            )
            ticket_box = InboundMailbox.objects.create(
                org=org_a, address="t@acme.test", is_active=False
            )
        set_modules_off(org_a, "leads")

        refused = admin_client.put(
            f"{MAILBOXES_URL}{leads_box.id}/", {"is_active": True}, format="json"
        )
        other_module = admin_client.put(
            f"{MAILBOXES_URL}{ticket_box.id}/", {"is_active": True}, format="json"
        )

        assert refused.status_code == 400
        assert refused.json()["errors"]["is_active"] == [
            "Leads is switched off for this organization."
        ]
        leads_box.refresh_from_db()
        assert leads_box.is_active is False
        assert other_module.status_code == 200, other_module.content

        set_modules_off(org_a)
        allowed = admin_client.put(
            f"{MAILBOXES_URL}{leads_box.id}/", {"is_active": True}, format="json"
        )
        assert allowed.status_code == 200, allowed.content

    def test_a_mailbox_can_be_switched_off_or_edited_while_its_module_is_off(
        self, admin_client, org_a
    ):
        with rls_org(org_a):
            box = InboundMailbox.objects.create(
                org=org_a, address="l@acme.test", creates="leads", is_active=True
            )
        set_modules_off(org_a, "leads")
        url = f"{MAILBOXES_URL}{box.id}/"

        edited = admin_client.put(
            url, {"lead_source_detail": "x", "is_active": True}, format="json"
        )
        off = admin_client.put(url, {"is_active": False}, format="json")

        assert edited.status_code == 200, edited.content
        assert off.status_code == 200, off.content

    def test_is_generated_is_not_writable(self, admin_client, org_a):
        data = _create(admin_client, address="s@acme.test", is_generated=True).json()
        assert data["is_generated"] is False


class TestGeneratedAddresses:
    def test_the_list_says_whether_addresses_can_be_generated(
        self, admin_client, org_a, settings
    ):
        settings.INBOUND_EMAIL_DOMAIN = ""
        assert admin_client.get(MAILBOXES_URL).json()["generated_domain"] is None

        settings.INBOUND_EMAIL_DOMAIN = "in.example.test"
        assert (
            admin_client.get(MAILBOXES_URL).json()["generated_domain"]
            == "in.example.test"
        )

    def test_generate_address_without_the_setting_is_400(
        self, admin_client, org_a, settings
    ):
        settings.INBOUND_EMAIL_DOMAIN = ""
        response = _create(admin_client, generate_address=True, creates="leads")

        assert response.status_code == 400
        assert "generate_address" in response.json()["errors"]
        assert not InboundMailbox.objects.filter(org=org_a).exists()

    def test_generate_address_makes_a_unique_routed_address(
        self, admin_client, org_a, settings
    ):
        settings.INBOUND_EMAIL_DOMAIN = "in.example.test"
        org_a.name = "Acme Homes & Co."
        org_a.save(update_fields=["name"])

        response = _create(
            admin_client, generate_address=True, provider="ses", creates="leads"
        )

        assert response.status_code == 201, response.content
        data = response.json()
        local, domain = data["address"].split("@")
        assert domain == "in.example.test"
        assert local.startswith("acme-homes-co-")
        suffix = local.removeprefix("acme-homes-co-")
        assert len(suffix) == 6 and suffix.isalnum() and suffix == suffix.lower()
        assert data["is_generated"] is True
        assert data["provider"] == "ses"
        assert PortalAccessToken.objects.filter(
            resource_type=PortalAccessToken.INBOUND_MAILBOX,
            resource_id=data["id"],
            token_hash=portal_token_hash(f"inbound-address:{data['address']}"),
        ).exists()

    def test_two_generated_addresses_differ(self, admin_client, org_a, settings):
        settings.INBOUND_EMAIL_DOMAIN = "in.example.test"
        first = _create(admin_client, generate_address=True).json()["address"]
        second = _create(admin_client, generate_address=True).json()["address"]
        assert first != second

    def test_a_clash_with_another_orgs_address_is_retried(
        self, admin_client, org_a, org_b, settings, monkeypatch
    ):
        settings.INBOUND_EMAIL_DOMAIN = "in.example.test"
        taken = "test-organization-a-aaaaaa@in.example.test"
        with rls_org(org_b):
            InboundMailbox.objects.create(org=org_b, address=taken, is_generated=True)
        suffixes = iter(["aaaaaa", "bbbbbb"])
        monkeypatch.setattr(
            "cases.inbound.generated._random_suffix", lambda: next(suffixes)
        )

        response = _create(admin_client, generate_address=True)

        assert response.status_code == 201, response.content
        assert response.json()["address"] == (
            "test-organization-a-bbbbbb@in.example.test"
        )

    def test_a_generated_address_ignores_a_typed_one_only_when_empty(
        self, admin_client, org_a, settings
    ):
        settings.INBOUND_EMAIL_DOMAIN = "in.example.test"
        response = _create(
            admin_client, generate_address=True, address="mine@acme.test"
        )
        assert response.status_code == 400
        assert "address" in response.json()["errors"]

    def test_an_address_is_required_when_not_generating(self, admin_client, org_a):
        response = _create(admin_client, creates="leads")
        assert response.status_code == 400
        assert "address" in response.json()["errors"]

    @pytest.mark.parametrize(
        "address",
        ["sales@in.example.test", "x@IN.EXAMPLE.TEST", "a@sub.in.example.test"],
    )
    def test_a_hand_typed_address_on_the_inbound_domain_is_refused(
        self, admin_client, org_a, settings, address
    ):
        settings.INBOUND_EMAIL_DOMAIN = "in.example.test"
        response = _create(admin_client, address=address)
        assert response.status_code == 400
        assert "address" in response.json()["errors"]

        with rls_org(org_a):
            mbx = InboundMailbox.objects.create(org=org_a, address="ok@acme.test")
        renamed = admin_client.put(
            f"{MAILBOXES_URL}{mbx.id}/", {"address": address}, format="json"
        )
        assert renamed.status_code == 400

    def test_a_typed_address_elsewhere_is_fine_with_the_setting(
        self, admin_client, org_a, settings
    ):
        settings.INBOUND_EMAIL_DOMAIN = "in.example.test"
        assert (
            _create(admin_client, address="notin.example.test@acme.test").status_code
            == 201
        )

    def test_a_generated_address_cannot_be_renamed_or_moved_off_ses(
        self, admin_client, org_a, settings
    ):
        settings.INBOUND_EMAIL_DOMAIN = "in.example.test"
        data = _create(admin_client, generate_address=True).json()
        url = f"{MAILBOXES_URL}{data['id']}/"

        same = admin_client.put(
            url,
            {"address": data["address"].upper(), "provider": "ses", "is_active": False},
            format="json",
        )
        renamed = admin_client.put(url, {"address": "x@acme.test"}, format="json")
        moved = admin_client.put(url, {"provider": "mailgun"}, format="json")

        assert same.status_code == 200, same.content
        assert renamed.status_code == 400
        assert moved.status_code == 400
        assert InboundMailbox.objects.get(pk=data["id"]).address == data["address"]

    def test_generate_address_on_an_edit_is_refused(
        self, admin_client, org_a, settings
    ):
        settings.INBOUND_EMAIL_DOMAIN = "in.example.test"
        with rls_org(org_a):
            mbx = InboundMailbox.objects.create(org=org_a, address="ok@acme.test")
        response = admin_client.put(
            f"{MAILBOXES_URL}{mbx.id}/", {"generate_address": True}, format="json"
        )
        assert response.status_code == 400

    def test_deleting_a_generated_mailbox_removes_its_routing(
        self, admin_client, org_a, settings
    ):
        settings.INBOUND_EMAIL_DOMAIN = "in.example.test"
        data = _create(admin_client, generate_address=True).json()
        admin_client.delete(f"{MAILBOXES_URL}{data['id']}/")
        assert not PortalAccessToken.objects.filter(resource_id=data["id"]).exists()


class TestModuleSwitch:
    URL = "/api/org/modules/"

    def _switch_off(self, client, *keys):
        return client.put(self.URL, {"off": list(keys), "order": []}, format="json")

    def test_leads_off_is_refused_while_a_lead_address_is_active(
        self, admin_client, org_a
    ):
        with rls_org(org_a):
            InboundMailbox.objects.create(
                org=org_a, address="leads@acme.test", creates="leads", is_active=True
            )
        response = self._switch_off(admin_client, "leads")

        assert response.status_code == 400
        assert response.json()["off"] == [
            "Leads still receives email at leads@acme.test. Switch that mailbox "
            "off first, so no email is lost."
        ]

    def test_a_lead_address_does_not_block_tickets_off(self, admin_client, org_a):
        with rls_org(org_a):
            InboundMailbox.objects.create(
                org=org_a, address="leads@acme.test", creates="leads", is_active=True
            )
        assert self._switch_off(admin_client, "tickets").status_code == 200


def test_a_lead_address_is_never_a_tickets_reply_to(us_org, mailbox, admin_user):
    """Ticket emails name the org's only receiving mailbox as Reply-To. A lead
    address must not be it, or customers' replies would become leads."""
    from cases.tasks import _reply_to_mailbox

    with rls_org(us_org):
        case = Case.objects.create(
            name="Printer", status="New", org=us_org, created_by=admin_user
        )
    assert _reply_to_mailbox(case) is None

    with rls_org(us_org):
        support = InboundMailbox.objects.create(
            org=us_org, address="support@acme.test", topic_arn=SNS_TOPIC
        )
    assert _reply_to_mailbox(case) == support
