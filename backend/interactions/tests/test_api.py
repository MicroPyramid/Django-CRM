"""`/api/interactions/`: logging, listing, editing and deleting, and who may.

Every permission test asserts both directions: the caller refused and the
caller let through.
"""

from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.test import APIClient

from accounts.models import Account
from cases.models import Case, CaseWatcher
from common.models import PersonalAccessToken
from common.testing import set_modules_off
from contacts.models import Contact
from interactions.models import Interaction
from leads.models import Lead
from opportunity.models import Opportunity
from webhooks.models import WebhookDelivery, WebhookEndpoint

URL = "/api/interactions/"


def _detail(interaction):
    return f"{URL}{interaction.id}/"


def _log(client, **body):
    return client.post(URL, {"kind": "call", **body}, format="json")


def _row(org, home, record, **fields):
    return Interaction.objects.create(
        org=org, home=home, **{"kind": "call", home: record, **fields}
    )


def _records(org, profile):
    """One record of each kind, each assigned to (or created for) `profile`."""
    lead = Lead.objects.create(org=org, first_name="Ada", status="assigned")
    contact = Contact.objects.create(org=org, first_name="Ann", last_name="Lee")
    account = Account.objects.create(org=org, name=f"Acme {profile.user.email}")
    deal = Opportunity.objects.create(org=org, name="Deal")
    case = Case.objects.create(org=org, name="Ticket", status="New", priority="Normal")
    for record in (lead, contact, account, deal, case):
        record.assigned_to.add(profile)
    return {
        "lead": lead,
        "contact": contact,
        "account": account,
        "opportunity": deal,
        "case": case,
    }


class TestCreate:
    def test_a_member_logs_a_call_on_a_lead_they_can_see(
        self, user_client, user_profile, lead
    ):
        response = _log(
            user_client,
            lead=str(lead.id),
            outcome="no_answer",
            duration_seconds=40,
            duration_estimated=True,
            body="Left a voicemail",
        )

        assert response.status_code == 201, response.content
        data = response.json()
        assert data["kind"] == "call"
        assert data["direction"] == "outbound"
        assert data["outcome"] == "no_answer"
        assert (data["duration_seconds"], data["duration_estimated"]) == (40, True)
        assert data["body"] == "Left a voicemail"
        assert data["home"] == "lead"
        assert data["lead"] == str(lead.id)
        assert data["contact"] is data["account"] is data["opportunity"] is None
        assert data["case"] is None
        assert data["origin"] == "manual"
        assert data["external_id"] == ""
        assert data["participants"] == []
        assert data["logged_by"] == str(user_profile.id)
        assert data["logged_by_details"] == {
            "id": str(user_profile.id),
            "name": user_profile.user.name,
            "email": user_profile.user.email,
        }
        assert data["can_edit"] is True

        lead.refresh_from_db()
        occurred = parse_datetime(data["occurred_at"])
        assert lead.first_response_at == occurred
        assert lead.first_response_by_id == user_profile.id
        assert lead.last_outbound_at == occurred
        assert lead.last_contacted == timezone.localdate(occurred)

    def test_who_logged_it_comes_from_the_caller_not_the_body(
        self, user_client, user_profile, admin_profile, lead, org_b
    ):
        response = _log(
            user_client,
            lead=str(lead.id),
            logged_by=str(admin_profile.id),
            org=str(org_b.id),
            external_id="X-1",
            participants=[{"name": "Someone"}],
            home="contact",
        )
        assert response.status_code == 201, response.content
        row = Interaction.objects.get(pk=response.json()["id"])
        assert row.logged_by_id == user_profile.id
        assert row.org_id == lead.org_id
        assert (row.home, row.external_id, row.participants) == ("lead", "", [])

    def test_a_lead_the_member_cannot_see_is_not_found(
        self, user_client, admin_client, hidden_lead
    ):
        refused = _log(user_client, lead=str(hidden_lead.id))
        assert refused.status_code == 404
        assert not Interaction.objects.exists()
        allowed = _log(admin_client, lead=str(hidden_lead.id))
        assert allowed.status_code == 201

    def test_another_orgs_lead_is_not_found(self, admin_client, org_b):
        other = Lead.objects.create(org=org_b, first_name="Elsewhere")
        assert _log(admin_client, lead=str(other.id)).status_code == 404
        assert not Interaction.objects.exists()

    def test_a_missing_or_malformed_id_is_refused(self, admin_client):
        missing = _log(admin_client, lead="6f1c2d3e-4a5b-4c6d-8e7f-901a2b3c4d5e")
        assert missing.status_code == 404
        assert _log(admin_client, lead="nope").status_code == 400

    @pytest.mark.parametrize(
        "home", ["lead", "contact", "account", "opportunity", "case"]
    )
    def test_each_record_kind_can_be_the_home(
        self, home, user_client, user_profile, org_a, admin_profile
    ):
        mine = _records(org_a, user_profile)[home]
        theirs = _records(org_a, admin_profile)[home]

        response = _log(user_client, **{home: str(mine.id)})
        assert response.status_code == 201, response.content
        assert response.json()["home"] == home
        assert response.json()[home] == str(mine.id)
        assert _log(user_client, **{home: str(theirs.id)}).status_code == 404

    def test_a_ticket_watcher_may_read_but_not_log(
        self, user_client, user_profile, org_a, admin_profile
    ):
        case = Case.objects.create(
            org=org_a, name="Ticket", status="New", priority="Normal"
        )
        CaseWatcher.objects.create(case=case, profile=user_profile, org=org_a)
        assert _log(user_client, case=str(case.id)).status_code == 403
        case.assigned_to.add(user_profile)
        assert _log(user_client, case=str(case.id)).status_code == 201

    def test_exactly_one_record(self, admin_client, org_a, admin_profile):
        records = _records(org_a, admin_profile)
        none = _log(admin_client)
        assert none.status_code == 400
        two = _log(
            admin_client,
            lead=str(records["lead"].id),
            contact=str(records["contact"].id),
        )
        assert two.status_code == 400
        assert not Interaction.objects.exists()

    def test_enquiry_is_the_systems_kind(self, admin_client, hidden_lead):
        response = _log(admin_client, lead=str(hidden_lead.id), kind="enquiry")
        assert response.status_code == 400
        assert "kind" in response.json()["errors"]
        for kind in ("call", "meeting", "email", "whatsapp", "sms"):
            ok = _log(admin_client, lead=str(hidden_lead.id), kind=kind)
            assert ok.status_code == 201, (kind, ok.content)

    def test_an_unknown_or_missing_kind_is_refused(self, admin_client, hidden_lead):
        assert _log(admin_client, lead=str(hidden_lead.id), kind="fax").status_code == (
            400
        )
        no_kind = admin_client.post(URL, {"lead": str(hidden_lead.id)}, format="json")
        assert no_kind.status_code == 400

    def test_a_time_more_than_five_minutes_ahead_is_refused(
        self, admin_client, hidden_lead
    ):
        ahead = timezone.now() + timedelta(minutes=10)
        response = _log(
            admin_client, lead=str(hidden_lead.id), occurred_at=ahead.isoformat()
        )
        assert response.status_code == 400
        assert "occurred_at" in response.json()["errors"]
        soon = timezone.now() + timedelta(minutes=4)
        ok = _log(admin_client, lead=str(hidden_lead.id), occurred_at=soon.isoformat())
        assert ok.status_code == 201

    def test_an_outcome_is_for_calls_only(self, admin_client, hidden_lead):
        meeting = _log(
            admin_client, lead=str(hidden_lead.id), kind="meeting", outcome="busy"
        )
        assert meeting.status_code == 400
        assert "outcome" in meeting.json()["errors"]
        unknown = _log(admin_client, lead=str(hidden_lead.id), outcome="maybe")
        assert unknown.status_code == 400
        call = _log(admin_client, lead=str(hidden_lead.id), outcome="busy")
        assert call.status_code == 201

    def test_origin_is_manual_or_phone_tap(self, admin_client, hidden_lead):
        tapped = _log(admin_client, lead=str(hidden_lead.id), origin="phone_tap")
        assert tapped.status_code == 201
        assert tapped.json()["origin"] == "phone_tap"
        for origin in ("intake", "email", "webform", "zapier"):
            refused = _log(admin_client, lead=str(hidden_lead.id), origin=origin)
            assert refused.status_code == 400, origin

    @pytest.mark.parametrize(
        "field,value",
        [
            ("subject", "s" * 201),
            ("body", "b" * 10_001),
            ("duration_seconds", -1),
            ("duration_seconds", "long"),
            ("direction", "sideways"),
            ("occurred_at", "yesterday"),
        ],
    )
    def test_malformed_fields_are_refused(
        self, admin_client, hidden_lead, field, value
    ):
        response = _log(admin_client, lead=str(hidden_lead.id), **{field: value})
        assert response.status_code == 400
        assert field in response.json()["errors"]

    def test_signed_out_is_refused(self, unauthenticated_client, hidden_lead):
        response = _log(unauthenticated_client, lead=str(hidden_lead.id))
        assert response.status_code in (401, 403)
        assert not Interaction.objects.exists()

    def test_an_off_module_is_not_found(self, admin_client, org_a, admin_profile):
        records = _records(org_a, admin_profile)
        set_modules_off(org_a, "leads", "deals", "tickets")
        for home in ("lead", "opportunity", "case"):
            response = _log(admin_client, **{home: str(records[home].id)})
            assert response.status_code == 404, home
            assert response.json()["code"] == "module_off"
        ok = _log(admin_client, contact=str(records["contact"].id))
        assert ok.status_code == 201

    def test_interaction_created_fires_and_lead_updated_does_not(
        self, user_client, lead, org_a, admin_profile
    ):
        hook = WebhookEndpoint.objects.create(
            org=org_a,
            url="https://hooks.example.com/in",
            events=["interaction.created", "lead.updated"],
            created_by=admin_profile.user,
        )
        with mock.patch("webhooks.emit.deliver_webhook.delay"):
            response = _log(user_client, lead=str(lead.id), body="Hi")
        assert response.status_code == 201
        deliveries = WebhookDelivery.objects.filter(endpoint=hook)
        assert list(deliveries.values_list("event", flat=True)) == [
            "interaction.created"
        ]
        data = deliveries.get().payload["data"]
        assert data["id"] == response.json()["id"]
        assert (data["kind"], data["home"], data["lead_id"]) == (
            "call",
            "lead",
            str(lead.id),
        )
        assert data["body"] == "Hi"


class TestList:
    def test_newest_first_with_a_count(self, user_client, lead, user_profile):
        now = timezone.now()
        old = _row(lead.org, "lead", lead, occurred_at=now - timedelta(days=2))
        new = _row(lead.org, "lead", lead, occurred_at=now - timedelta(hours=1))
        middle = _row(lead.org, "lead", lead, occurred_at=now - timedelta(days=1))

        response = user_client.get(URL, {"lead": str(lead.id)})

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert [r["id"] for r in data["interactions"]] == [
            str(new.id),
            str(middle.id),
            str(old.id),
        ]

    def test_limit_and_offset(self, user_client, lead):
        now = timezone.now()
        rows = [
            _row(lead.org, "lead", lead, occurred_at=now - timedelta(minutes=i))
            for i in range(5)
        ]
        page = user_client.get(URL, {"lead": str(lead.id), "limit": 2, "offset": 1})
        assert page.status_code == 200
        assert page.json()["count"] == 5
        assert [r["id"] for r in page.json()["interactions"]] == [
            str(rows[1].id),
            str(rows[2].id),
        ]

    def test_the_limit_is_capped_and_bad_paging_falls_back(self, user_client, lead):
        _row(lead.org, "lead", lead)
        _row(lead.org, "lead", lead)
        with mock.patch("interactions.views.MAX_LIMIT", 1):
            capped = user_client.get(URL, {"lead": str(lead.id), "limit": 500})
        assert capped.status_code == 200
        assert len(capped.json()["interactions"]) == 1
        for params in ({"limit": "x"}, {"limit": -3}, {"offset": "y"}):
            response = user_client.get(URL, {"lead": str(lead.id), **params})
            assert response.status_code == 200, params
            assert len(response.json()["interactions"]) == 2

    def test_exactly_one_record_filter(self, user_client, lead, org_a):
        contact = Contact.objects.create(org=org_a, first_name="A", last_name="B")
        assert user_client.get(URL).status_code == 400
        both = user_client.get(URL, {"lead": str(lead.id), "contact": str(contact.id)})
        assert both.status_code == 400
        assert user_client.get(URL, {"lead": "nope"}).status_code == 400

    def test_a_record_the_caller_cannot_open_is_not_found(
        self, user_client, admin_client, hidden_lead
    ):
        _row(hidden_lead.org, "lead", hidden_lead)
        assert user_client.get(URL, {"lead": str(hidden_lead.id)}).status_code == 404
        allowed = admin_client.get(URL, {"lead": str(hidden_lead.id)})
        assert allowed.status_code == 200
        assert allowed.json()["count"] == 1

    def test_another_orgs_record_is_not_found(self, admin_client, org_b):
        other = Lead.objects.create(org=org_b, first_name="Elsewhere")
        _row(org_b, "lead", other)
        assert admin_client.get(URL, {"lead": str(other.id)}).status_code == 404

    def test_a_timeline_lists_only_what_the_caller_may_open(
        self, user_client, admin_client, user_profile, hidden_lead, org_a
    ):
        contact = Contact.objects.create(org=org_a, first_name="Ann", last_name="Lee")
        contact.assigned_to.add(user_profile)
        own = _row(org_a, "contact", contact)
        # Homed on a lead the member cannot open, and linked to the contact.
        elsewhere = _row(org_a, "lead", hidden_lead, contact=contact)

        mine = user_client.get(URL, {"contact": str(contact.id)}).json()
        assert [r["id"] for r in mine["interactions"]] == [str(own.id)]
        assert mine["count"] == 1
        everything = admin_client.get(URL, {"contact": str(contact.id)}).json()
        assert {r["id"] for r in everything["interactions"]} == {
            str(own.id),
            str(elsewhere.id),
        }

    @pytest.mark.parametrize(
        "home", ["lead", "contact", "account", "opportunity", "case"]
    )
    def test_each_record_kind_filters(self, home, admin_client, org_a, admin_profile):
        records = _records(org_a, admin_profile)
        target = records[home]
        row = _row(org_a, home, target)
        elsewhere = "account" if home == "contact" else "contact"
        _row(org_a, elsewhere, records[elsewhere])

        response = admin_client.get(URL, {home: str(target.id)})
        assert response.status_code == 200
        assert [r["id"] for r in response.json()["interactions"]] == [str(row.id)]

    def test_an_off_module_hides_its_homes_and_its_timeline(
        self, admin_client, org_a, admin_profile
    ):
        records = _records(org_a, admin_profile)
        contact = records["contact"]
        on_contact = _row(org_a, "contact", contact)
        on_deal = _row(org_a, "opportunity", records["opportunity"], contact=contact)
        before = admin_client.get(URL, {"contact": str(contact.id)}).json()
        assert {r["id"] for r in before["interactions"]} == {
            str(on_contact.id),
            str(on_deal.id),
        }

        set_modules_off(org_a, "deals")
        after = admin_client.get(URL, {"contact": str(contact.id)}).json()
        assert [r["id"] for r in after["interactions"]] == [str(on_contact.id)]
        off = admin_client.get(URL, {"opportunity": str(records["opportunity"].id)})
        assert off.status_code == 404
        assert off.json()["code"] == "module_off"

    def test_can_edit_is_the_callers(
        self, user_client, admin_client, user_profile, colleague, lead
    ):
        mine = _row(lead.org, "lead", lead, logged_by=user_profile)
        theirs = _row(lead.org, "lead", lead, logged_by=colleague)
        enquiry = _row(
            lead.org, "lead", lead, kind="enquiry", direction="inbound", origin="intake"
        )

        def flags(client):
            rows = client.get(URL, {"lead": str(lead.id)}).json()["interactions"]
            return {r["id"]: r["can_edit"] for r in rows}

        assert flags(user_client) == {
            str(mine.id): True,
            str(theirs.id): False,
            str(enquiry.id): False,
        }
        assert flags(admin_client) == {
            str(mine.id): True,
            str(theirs.id): True,
            str(enquiry.id): False,
        }


class TestEdit:
    def test_another_member_is_refused_and_an_admin_allowed(
        self, colleague_client, admin_client, user_profile, lead
    ):
        row = _row(lead.org, "lead", lead, logged_by=user_profile, body="first")

        refused = colleague_client.patch(_detail(row), {"body": "x"}, format="json")
        assert refused.status_code == 403
        row.refresh_from_db()
        assert row.body == "first"

        allowed = admin_client.patch(_detail(row), {"body": "edited"}, format="json")
        assert allowed.status_code == 200, allowed.content
        assert allowed.json()["body"] == "edited"
        row.refresh_from_db()
        assert row.body == "edited"
        # Who logged it does not change hands with the edit.
        assert row.logged_by_id == user_profile.id

    def test_the_logger_edits_their_own(self, user_client, user_profile, lead):
        row = _row(lead.org, "lead", lead, logged_by=user_profile)
        response = user_client.patch(
            _detail(row),
            {"outcome": "connected", "duration_seconds": None, "subject": "Intro"},
            format="json",
        )
        assert response.status_code == 200, response.content
        row.refresh_from_db()
        assert (row.outcome, row.duration_seconds, row.subject) == (
            "connected",
            None,
            "Intro",
        )

    def test_a_record_the_caller_cannot_open_is_not_found(
        self, user_client, user_profile, hidden_lead, admin_client
    ):
        # Logged by the member, who has since lost the lead.
        row = _row(hidden_lead.org, "lead", hidden_lead, logged_by=user_profile)
        assert user_client.patch(
            _detail(row), {"body": "x"}, format="json"
        ).status_code == (404)
        assert user_client.delete(_detail(row)).status_code == 404
        ok = admin_client.patch(_detail(row), {"body": "x"}, format="json")
        assert ok.status_code == 200

    def test_another_orgs_interaction_is_not_found(self, admin_client, org_b):
        other = Lead.objects.create(org=org_b, first_name="Elsewhere")
        row = _row(org_b, "lead", other, body="theirs")
        assert admin_client.patch(
            _detail(row), {"body": "x"}, format="json"
        ).status_code == (404)
        assert admin_client.delete(_detail(row)).status_code == 404
        assert admin_client.patch(f"{URL}nope/", {}, format="json").status_code == 404
        row.refresh_from_db()
        assert (row.body, row.org_id, row.lead_id) == ("theirs", org_b.id, other.id)

    @pytest.mark.parametrize(
        "fields",
        [
            {"kind": "enquiry", "direction": "inbound", "origin": "intake"},
            {"kind": "call", "origin": "zapier"},
            {"kind": "email", "origin": "email"},
        ],
    )
    def test_enquiries_and_system_rows_are_read_only(
        self, admin_client, admin_profile, hidden_lead, fields
    ):
        row = _row(
            hidden_lead.org, "lead", hidden_lead, logged_by=admin_profile, **fields
        )
        assert admin_client.patch(
            _detail(row), {"body": "x"}, format="json"
        ).status_code == (403)
        assert admin_client.delete(_detail(row)).status_code == 403
        assert Interaction.objects.filter(pk=row.pk).exists()
        manual = _row(hidden_lead.org, "lead", hidden_lead, logged_by=admin_profile)
        assert (
            admin_client.patch(
                _detail(manual), {"body": "x"}, format="json"
            ).status_code
            == 200
        )

    def test_the_home_and_kind_stay_put(self, user_client, user_profile, lead, org_a):
        row = _row(lead.org, "lead", lead, logged_by=user_profile)
        contact = Contact.objects.create(org=org_a, first_name="A", last_name="B")
        contact.assigned_to.add(user_profile)
        for body in (
            {"kind": "meeting"},
            {"home": "contact"},
            {"contact": str(contact.id)},
            {"lead": None},
        ):
            response = user_client.patch(_detail(row), body, format="json")
            assert response.status_code == 400, body
        # Sending back what is already there is fine.
        same = user_client.patch(
            _detail(row),
            {"kind": "call", "home": "lead", "lead": str(lead.id), "contact": None},
            format="json",
        )
        assert same.status_code == 200, same.content
        row.refresh_from_db()
        assert (row.kind, row.home, row.lead_id, row.contact_id) == (
            "call",
            "lead",
            lead.id,
            None,
        )

    def test_the_rules_of_create_apply(self, user_client, user_profile, lead):
        meeting = _row(lead.org, "lead", lead, logged_by=user_profile, kind="meeting")
        outcome = user_client.patch(
            _detail(meeting), {"outcome": "busy"}, format="json"
        )
        assert outcome.status_code == 400
        ahead = (timezone.now() + timedelta(minutes=10)).isoformat()
        future = user_client.patch(
            _detail(meeting), {"occurred_at": ahead}, format="json"
        )
        assert future.status_code == 400
        origin = user_client.patch(
            _detail(meeting), {"origin": "intake"}, format="json"
        )
        assert origin.status_code == 400
        tapped = user_client.patch(
            _detail(meeting), {"origin": "phone_tap"}, format="json"
        )
        assert tapped.status_code == 200

    def test_put_is_not_offered(self, user_client, user_profile, lead):
        row = _row(lead.org, "lead", lead, logged_by=user_profile)
        response = user_client.put(_detail(row), {"kind": "call"}, format="json")
        assert response.status_code == 405


class TestDelete:
    def test_another_member_is_refused_and_the_logger_allowed(
        self, colleague_client, user_client, user_profile, lead
    ):
        row = _row(lead.org, "lead", lead, logged_by=user_profile)
        assert colleague_client.delete(_detail(row)).status_code == 403
        assert Interaction.objects.filter(pk=row.pk).exists()
        assert user_client.delete(_detail(row)).status_code == 204
        assert not Interaction.objects.filter(pk=row.pk).exists()

    def test_an_admin_deletes_anyones(self, admin_client, user_profile, lead):
        row = _row(lead.org, "lead", lead, logged_by=user_profile)
        assert admin_client.delete(_detail(row)).status_code == 204
        assert not Interaction.objects.filter(pk=row.pk).exists()


def _token_client(profile, scopes):
    raw, _ = PersonalAccessToken.generate(profile=profile, name="cli", scopes=scopes)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {raw}")
    return client


class TestTokenScopes:
    """A token needs the home record's own scope besides `interactions:*`, the
    scope that record's comments need. Sessions are not scoped."""

    def test_reading_a_lead_timeline_needs_leads_read(self, user_profile, lead):
        _row(lead.org, "lead", lead)
        narrow = _token_client(user_profile, ["interactions:read"])
        refused = narrow.get(URL, {"lead": str(lead.id)})
        assert refused.status_code == 403
        assert "leads:read" in refused.json()["detail"]
        wide = _token_client(user_profile, ["interactions:read", "leads:read"])
        allowed = wide.get(URL, {"lead": str(lead.id)})
        assert allowed.status_code == 200
        assert allowed.json()["count"] == 1

    def test_logging_on_a_lead_needs_leads_write(self, user_profile, lead):
        narrow = _token_client(user_profile, ["interactions:write"])
        refused = _log(narrow, lead=str(lead.id))
        assert refused.status_code == 403
        assert "leads:write" in refused.json()["detail"]
        assert not Interaction.objects.exists()
        wide = _token_client(user_profile, ["interactions:write", "leads:write"])
        assert _log(wide, lead=str(lead.id)).status_code == 201

    def test_changing_and_deleting_need_the_homes_write_scope(self, user_profile, lead):
        row = _row(lead.org, "lead", lead, logged_by=user_profile, body="kept")
        narrow = _token_client(user_profile, ["interactions:write"])
        assert narrow.patch(_detail(row), {"body": "x"}, format="json").status_code == (
            403
        )
        assert narrow.delete(_detail(row)).status_code == 403
        row.refresh_from_db()
        assert row.body == "kept"

        wide = _token_client(user_profile, ["interactions:write", "leads:write"])
        changed = wide.patch(_detail(row), {"body": "edited"}, format="json")
        assert changed.status_code == 200
        assert wide.delete(_detail(row)).status_code == 204
        assert not Interaction.objects.filter(pk=row.pk).exists()

    def test_a_timeline_leaves_out_homes_the_token_cannot_read(
        self, user_profile, lead, org_a
    ):
        contact = Contact.objects.create(org=org_a, first_name="Ann", last_name="Lee")
        contact.assigned_to.add(user_profile)
        own = _row(org_a, "contact", contact)
        on_lead = _row(org_a, "lead", lead, contact=contact)

        narrow = _token_client(user_profile, ["interactions:read", "contacts:read"])
        rows = narrow.get(URL, {"contact": str(contact.id)}).json()
        assert [r["id"] for r in rows["interactions"]] == [str(own.id)]
        assert rows["count"] == 1
        wide = _token_client(
            user_profile, ["interactions:read", "contacts:read", "leads:read"]
        )
        rows = wide.get(URL, {"contact": str(contact.id)}).json()
        assert {r["id"] for r in rows["interactions"]} == {str(own.id), str(on_lead.id)}

    def test_an_unscoped_token_a_wildcard_and_a_session_are_not_limited(
        self, user_profile, user_client, lead
    ):
        _row(lead.org, "lead", lead)
        for client in (
            _token_client(user_profile, []),
            _token_client(user_profile, ["*:read"]),
            user_client,
        ):
            response = client.get(URL, {"lead": str(lead.id)})
            assert response.status_code == 200
            assert response.json()["count"] == 1

    def test_the_org_key_reads_and_cannot_write(self, org_a, admin_profile, lead):
        _row(org_a, "lead", lead)
        key = APIClient()
        key.credentials(HTTP_TOKEN=org_a.api_key)
        listed = key.get(URL, {"lead": str(lead.id)})
        assert listed.status_code == 200
        assert listed.json()["count"] == 1
        assert _log(key, lead=str(lead.id)).status_code == 403
        assert Interaction.objects.count() == 1
