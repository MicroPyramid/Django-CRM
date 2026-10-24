"""Each arrival through `receive_lead` is an `enquiry` interaction, and
converting a lead moves its interactions home to the contact it became."""

from datetime import timedelta

import pytest
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from accounts.models import Account
from common.models import Comment
from common.testing import set_modules_off
from contacts.models import Contact
from interactions.models import Interaction
from interactions.service import log_interaction
from leads.intake import IncomingLead, receive_lead
from leads.models import Lead
from opportunity.models import Opportunity

SOURCE = "intake:11111111-1111-4111-8111-111111111111"
URL = "/api/interactions/"


def incoming(**overrides):
    fields = {
        "values": {"first_name": "Pat", "email": "pat@example.com"},
        "custom_fields": {},
        "source": "google ads",
        "external_source": SOURCE,
        "channel_label": "webhook Ads",
    }
    fields.update(overrides)
    return IncomingLead(**fields)


def run(org, data, capture):
    with capture(execute=True):
        return receive_lead(org, data)


def enquiries(**links):
    return Interaction.objects.filter(kind="enquiry", **links).order_by("created_at")


def comments_on(record):
    return Comment.objects.filter(
        content_type=ContentType.objects.get_for_model(type(record)),
        object_id=record.id,
    )


@pytest.fixture
def us_org(org_a):
    org_a.default_country = "US"
    org_a.save(update_fields=["default_country"])
    return org_a


@pytest.fixture
def known(org_a):
    return Lead.objects.create(
        org=org_a, email="pat@example.com", first_name="Pat", status="in process"
    )


class TestArrivals:
    def test_a_new_lead_gets_its_enquiry_and_no_comment(
        self, org_a, django_capture_on_commit_callbacks
    ):
        result = run(
            org_a,
            incoming(enquiry_text="Wants a quote"),
            django_capture_on_commit_callbacks,
        )
        lead = Lead.objects.get(pk=result.lead.pk)
        row = enquiries(lead=lead).get()
        assert (row.home, row.lead_id, row.contact_id, row.account_id) == (
            "lead",
            lead.id,
            None,
            None,
        )
        assert (row.direction, row.logged_by_id, row.origin) == (
            "inbound",
            None,
            "intake",
        )
        assert (row.subject, row.body) == ("webhook Ads", "Wants a quote")
        assert row.occurred_at == lead.last_enquiry_at
        assert row.org_id == org_a.id
        assert comments_on(lead).count() == 0
        # An enquiry is the lead asking, not anyone answering.
        assert (lead.first_response_at, lead.last_outbound_at) == (None, None)

    def test_a_mapped_description_keeps_the_whole_message_on_the_enquiry(
        self, org_a, django_capture_on_commit_callbacks
    ):
        result = run(
            org_a,
            incoming(
                values={"email": "pat@example.com", "description": "Hello"},
                enquiry_text="Budget: 5000",
            ),
            django_capture_on_commit_callbacks,
        )
        assert result.lead.description == "Hello"
        assert enquiries(lead=result.lead).get().body == "Budget: 5000"
        assert comments_on(result.lead).count() == 0

    def test_a_repeat_enquiry_is_a_second_enquiry(
        self, org_a, known, django_capture_on_commit_callbacks
    ):
        run(
            org_a,
            incoming(enquiry_text="Second ask"),
            django_capture_on_commit_callbacks,
        )
        row = enquiries(lead=known).get()
        assert row.body == "Second ask"
        assert row.home == "lead"
        assert comments_on(known).count() == 0
        run(org_a, incoming(enquiry_text="Third"), django_capture_on_commit_callbacks)
        assert [r.body for r in enquiries(lead=known)] == ["Second ask", "Third"]

    def test_what_the_lead_did_not_take_is_kept_in_the_enquiry(
        self, us_org, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(org=us_org, phone="+1 (555) 123-4567")
        run(
            us_org,
            incoming(
                values={"phone": "555-123-4567", "email": "pat@example.com"},
                enquiry_text="Call me",
            ),
            django_capture_on_commit_callbacks,
        )
        body = enquiries(lead=lead).get().body
        assert "Call me" in body
        assert "Email: pat@example.com" in body

    def test_an_arrival_with_no_text_is_still_an_enquiry(
        self, org_a, known, django_capture_on_commit_callbacks
    ):
        run(org_a, incoming(enquiry_text=""), django_capture_on_commit_callbacks)
        assert enquiries(lead=known).get().body == ""

    def test_a_long_enquiry_is_cut_to_fit(
        self, org_a, known, django_capture_on_commit_callbacks
    ):
        run(
            org_a,
            incoming(enquiry_text="x" * 30_000),
            django_capture_on_commit_callbacks,
        )
        body = enquiries(lead=known).get().body
        assert len(body) == 10_000
        assert body.endswith("…")

    def test_a_retry_is_not_a_second_enquiry(
        self, org_a, django_capture_on_commit_callbacks
    ):
        first = run(
            org_a, incoming(external_id="L-1"), django_capture_on_commit_callbacks
        )
        again = run(
            org_a,
            incoming(external_id="L-1", enquiry_text="again"),
            django_capture_on_commit_callbacks,
        )
        assert again.result == "duplicate"
        assert enquiries(lead=first.lead).count() == 1

    @pytest.mark.parametrize(
        "external_source,origin",
        [
            (SOURCE, "intake"),
            ("webform:22222222-2222-4222-8222-222222222222", "webform"),
            ("email:33333333-3333-4333-8333-333333333333", "email"),
            ("", "intake"),
        ],
    )
    def test_the_origin_follows_the_route(
        self, org_a, external_source, origin, django_capture_on_commit_callbacks
    ):
        result = run(
            org_a,
            incoming(external_source=external_source),
            django_capture_on_commit_callbacks,
        )
        assert enquiries(lead=result.lead).get().origin == origin

    def test_a_late_arrival_is_recorded_at_its_own_time(
        self, org_a, known, django_capture_on_commit_callbacks
    ):
        when = timezone.now() - timedelta(days=3)
        run(org_a, incoming(occurred_at=when), django_capture_on_commit_callbacks)
        assert enquiries(lead=known).get().occurred_at == when

    def test_an_enquiry_does_not_touch_an_answered_lead(
        self, org_a, known, user_profile, django_capture_on_commit_callbacks
    ):
        call = log_interaction(
            org_a, home="lead", record=known, kind="call", logged_by=user_profile
        )
        run(org_a, incoming(), django_capture_on_commit_callbacks)
        known.refresh_from_db()
        assert known.first_response_at == call.occurred_at
        assert known.last_outbound_at == call.occurred_at
        assert known.last_enquiry_at > call.occurred_at


class TestConvertedLeads:
    def test_the_enquiry_lands_on_the_contact_and_its_account(
        self, org_a, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(
            org=org_a, email="pat@example.com", status="converted", first_name="Pat"
        )
        account = Account.objects.create(org=org_a, name="Acme")
        contact = Contact.objects.create(
            org=org_a,
            first_name="Pat",
            last_name="P",
            email="PAT@example.com",
            account=account,
        )

        result = run(
            org_a,
            incoming(enquiry_text="Back again"),
            django_capture_on_commit_callbacks,
        )

        assert result.contact.pk == contact.pk
        row = enquiries(contact=contact).get()
        assert (row.home, row.contact_id, row.account_id, row.lead_id) == (
            "contact",
            contact.id,
            account.id,
            lead.id,
        )
        assert row.body == "Back again"
        assert comments_on(contact).count() == 0
        assert comments_on(lead).count() == 0

    def test_without_a_contact_it_stays_on_the_lead(
        self, org_a, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(
            org=org_a, email="pat@example.com", status="converted", first_name="Pat"
        )
        run(org_a, incoming(), django_capture_on_commit_callbacks)
        row = enquiries(lead=lead).get()
        assert (row.home, row.contact_id) == ("lead", None)


class TestConversion:
    def _convert(self, client, lead):
        return client.patch(
            f"/api/leads/{lead.id}/", {"status": "converted"}, format="json"
        )

    def test_interactions_move_home_to_the_contact_and_gain_the_account_and_deal(
        self, admin_client, user_client, lead, user_profile, org_a
    ):
        call = log_interaction(
            org_a, home="lead", record=lead, kind="call", logged_by=user_profile
        )
        enquiry = log_interaction(
            org_a,
            home="lead",
            record=lead,
            kind="enquiry",
            direction="inbound",
            origin="webform",
        )

        response = self._convert(admin_client, lead)

        assert response.status_code == 200, response.content
        contact = Contact.objects.get(org=org_a, email__iexact=lead.email)
        deal = Opportunity.objects.get(org=org_a)
        for row in (call, enquiry):
            row.refresh_from_db()
            assert (
                row.home,
                row.lead_id,
                row.contact_id,
                row.account_id,
                row.opportunity_id,
            ) == ("contact", lead.id, contact.id, contact.account_id, deal.id)
        assert contact.account_id is not None
        # The lead's owner keeps the history, now through the contact.
        listed = user_client.get(URL, {"contact": str(contact.id)}).json()
        assert listed["count"] == 2
        on_lead = user_client.get(URL, {"lead": str(lead.id)}).json()
        assert on_lead["count"] == 2
        lead.refresh_from_db()
        assert lead.first_response_by_id == user_profile.id

    def test_with_deals_off_there_is_no_deal_to_link(
        self, admin_client, lead, user_profile, org_a
    ):
        set_modules_off(org_a, "deals")
        call = log_interaction(
            org_a, home="lead", record=lead, kind="call", logged_by=user_profile
        )
        assert self._convert(admin_client, lead).status_code == 200
        call.refresh_from_db()
        assert call.home == "contact"
        assert call.opportunity_id is None

    def test_with_no_contact_to_move_to_the_account_is_home(
        self, user_client, lead, user_profile, org_a, admin_profile
    ):
        # A contact with the lead's email that the member may not open: the
        # conversion leaves it alone and makes no contact of its own.
        stranger = Contact.objects.create(
            org=org_a, first_name="Some", last_name="One", email=lead.email
        )
        stranger.assigned_to.add(admin_profile)
        call = log_interaction(
            org_a, home="lead", record=lead, kind="call", logged_by=user_profile
        )

        response = self._convert(user_client, lead)

        assert response.status_code == 200, response.content
        account = Account.objects.get(org=org_a)
        call.refresh_from_db()
        assert (call.home, call.account_id, call.contact_id, call.lead_id) == (
            "account",
            account.id,
            None,
            lead.id,
        )
        listed = user_client.get(URL, {"account": str(account.id)}).json()
        assert listed["count"] == 1

    def test_another_leads_interactions_stay_put(
        self, admin_client, lead, org_a, user_profile
    ):
        other = Lead.objects.create(org=org_a, first_name="Other", status="assigned")
        row = log_interaction(
            org_a, home="lead", record=other, kind="call", logged_by=user_profile
        )
        assert self._convert(admin_client, lead).status_code == 200
        row.refresh_from_db()
        assert (row.home, row.contact_id, row.account_id) == ("lead", None, None)
