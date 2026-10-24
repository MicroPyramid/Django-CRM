"""Lead handling release 1 foundation: the new columns and tables, the default
lead sources, the data migrations, and phone matching by E.164."""

import importlib
from types import SimpleNamespace

import pytest
from django.apps import apps as global_apps
from django.db import IntegrityError, connection, transaction

from automation.models import AutomationRule
from cases.models import InboundMailbox
from common.duplicate_detection import find_duplicates, merge_records
from common.models import SavedView, Tags
from common.testing import clear_rls_context, rls_org, set_rls_context
from contacts.access import visible_contacts_qs
from contacts.models import Contact
from leads.access import visible_leads_qs
from leads.models import Lead, LeadIntake, LeadIntakeEvent, LeadSource
from leads.sources import DEFAULT_SOURCES, org_sources, source_keys, source_labels
from opportunity.models import Opportunity
from webforms.models import WebForm


def _run(module_name, function):
    """Call a data migration's own function, the way test_tag_slugs.py does.
    The live models stand in for the historical ones; the fields it touches
    are the same."""
    module = importlib.import_module(module_name)
    getattr(module, function)(global_apps, SimpleNamespace(connection=connection))


def _us(org):
    org.default_country = "US"
    org.save(update_fields=["default_country"])
    return org


def _lead(org, **fields):
    return Lead.objects.create(org=org, first_name="Ada", last_name="L", **fields)


# ---------------------------------------------------------------------------
# phone_e164 on save
# ---------------------------------------------------------------------------


class TestPhoneE164OnSave:
    def test_saving_a_lead_sets_phone_e164_with_the_orgs_country(self, org_a):
        lead = _lead(_us(org_a), phone="(555) 123-4567")
        lead.refresh_from_db()
        assert lead.phone_e164 == "+15551234567"

    def test_a_local_number_in_an_org_with_no_country_stays_empty(self, org_a):
        lead = _lead(org_a, phone="555-123-4567")
        lead.refresh_from_db()
        assert lead.phone_e164 == ""

    def test_an_international_number_needs_no_country(self, org_a):
        lead = _lead(org_a, phone="+44 20 7946 0958")
        lead.refresh_from_db()
        assert lead.phone_e164 == "+442079460958"

    def test_changing_and_clearing_the_phone_follow(self, org_a):
        lead = _lead(_us(org_a), phone="555-123-4567")
        lead.phone = "555-987-6543"
        lead.save()
        lead.refresh_from_db()
        assert lead.phone_e164 == "+15559876543"
        lead.phone = ""
        lead.save()
        lead.refresh_from_db()
        assert lead.phone_e164 == ""

    def test_update_fields_with_phone_also_writes_phone_e164(self, org_a):
        lead = _lead(_us(org_a), phone="555-123-4567")
        lead.phone = "555-987-6543"
        lead.save(update_fields=["phone"])
        lead.refresh_from_db()
        assert lead.phone_e164 == "+15559876543"

    def test_update_fields_without_phone_leaves_phone_e164_alone(self, org_a):
        lead = _lead(_us(org_a), phone="555-123-4567")
        Lead.objects.filter(pk=lead.pk).update(phone_e164="")
        lead.refresh_from_db()
        lead.title = "Renamed"
        lead.save(update_fields=["title"])
        lead.refresh_from_db()
        assert lead.phone_e164 == ""

    def test_saving_a_contact_sets_phone_e164(self, org_a):
        contact = Contact.objects.create(
            org=_us(org_a), first_name="Ada", last_name="L", phone="555.123.4567"
        )
        contact.refresh_from_db()
        assert contact.phone_e164 == "+15551234567"


# ---------------------------------------------------------------------------
# New lead columns and the external id key
# ---------------------------------------------------------------------------


class TestLeadColumns:
    def test_new_columns_default_to_empty(self, org_a):
        lead = _lead(org_a)
        lead.refresh_from_db()
        assert lead.source_detail == ""
        assert lead.source_ref == ""
        assert lead.external_source == ""
        assert lead.external_id == ""
        assert lead.last_enquiry_at is None

    def test_source_takes_a_key_outside_the_legacy_seven(self, org_a):
        lead = _lead(org_a, source="google ads")
        lead.refresh_from_db()
        assert lead.source == "google ads"

    def test_a_repeated_external_id_from_one_source_is_refused(self, org_a):
        _lead(org_a, external_source="intake:1", external_id="abc")
        with pytest.raises(IntegrityError), transaction.atomic():
            Lead.objects.create(
                org=org_a,
                first_name="Bo",
                external_source="intake:1",
                external_id="abc",
            )

    def test_empty_external_ids_never_clash(self, org_a):
        _lead(org_a, external_source="intake:1")
        Lead.objects.create(org=org_a, first_name="Bo", external_source="intake:1")
        assert Lead.objects.filter(org=org_a).count() == 2

    def test_the_same_external_id_from_another_source_is_fine(self, org_a):
        _lead(org_a, external_source="intake:1", external_id="abc")
        Lead.objects.create(
            org=org_a, first_name="Bo", external_source="intake:2", external_id="abc"
        )
        assert Lead.objects.filter(org=org_a, external_id="abc").count() == 2

    def test_the_same_external_id_in_another_org_is_fine(self, org_a, org_b):
        _lead(org_a, external_source="intake:1", external_id="abc")
        with rls_org(org_b):
            _lead(org_b, external_source="intake:1", external_id="abc")
        assert Lead.objects.filter(org=org_a, external_id="abc").count() == 1

    def test_deal_gains_sub_source_and_reference(self, org_a):
        deal = Opportunity.objects.create(
            org=org_a,
            name="Deal",
            lead_source="google ads",
            source_detail="Spring",
            source_ref="ad-42",
        )
        deal.refresh_from_db()
        assert (deal.lead_source, deal.source_detail, deal.source_ref) == (
            "google ads",
            "Spring",
            "ad-42",
        )
        assert Opportunity.objects.create(org=org_a, name="Bare").source_detail == ""

    def test_contact_gains_source_columns(self, org_a):
        contact = Contact.objects.create(
            org=org_a,
            first_name="Ada",
            last_name="L",
            source="referral",
            source_detail="Spring open day",
            source_ref="ad-42",
        )
        contact.refresh_from_db()
        assert (contact.source, contact.source_detail, contact.source_ref) == (
            "referral",
            "Spring open day",
            "ad-42",
        )


# ---------------------------------------------------------------------------
# Lead sources
# ---------------------------------------------------------------------------


class TestOrgSources:
    def test_the_defaults_are_the_fifteen_listed(self):
        assert len(DEFAULT_SOURCES) == 15
        assert dict(DEFAULT_SOURCES)["web form"] == "Web form"
        assert "compaign" not in dict(DEFAULT_SOURCES)

    def test_first_use_creates_the_defaults_in_order(self, org_a):
        sources = org_sources(org_a)
        assert [(s.key, s.label) for s in sources] == list(DEFAULT_SOURCES)
        assert all(s.is_active for s in sources)
        assert [s.order for s in sources] == list(range(15))

    def test_a_second_call_creates_nothing(self, org_a):
        org_sources(org_a)
        org_sources(org_a)
        assert LeadSource.objects.filter(org=org_a).count() == 15

    def test_each_org_gets_its_own(self, org_a, org_b):
        org_sources(org_a)
        with rls_org(org_b):
            assert len(org_sources(org_b)) == 15
            assert LeadSource.objects.filter(org=org_b).count() == 15
        assert LeadSource.objects.filter(org=org_a).count() == 15

    def test_an_org_with_an_added_source_still_gets_the_defaults(self, org_a):
        LeadSource.objects.create(
            org=org_a, key="property portal", label="Property portal", order=15
        )
        keys = [s.key for s in org_sources(org_a)]
        assert len(keys) == 16
        assert keys[-1] == "property portal"

    def test_a_renamed_default_keeps_its_label(self, org_a):
        org_sources(org_a)
        LeadSource.objects.filter(org=org_a, key="call").update(label="Phone call")
        assert dict(source_labels(org_a))["call"] == "Phone call"
        assert LeadSource.objects.filter(org=org_a).count() == 15

    def test_source_keys_leaves_out_retired_ones_unless_asked(self, org_a):
        org_sources(org_a)
        LeadSource.objects.filter(org=org_a, key="partner").update(is_active=False)
        assert "partner" not in source_keys(org_a)
        assert "partner" in source_keys(org_a, active_only=False)
        assert "google ads" in source_keys(org_a)

    def test_reading_keys_and_labels_writes_nothing(self, org_a):
        assert "google ads" in source_keys(org_a)
        assert source_labels(org_a)["walk-in"] == "Walk-in"
        assert not LeadSource.objects.filter(org=org_a).exists()

    def test_the_read_only_list_merges_stored_and_unsaved_defaults(self, org_a):
        LeadSource.objects.create(
            org=org_a, key="property portal", label="Property portal", order=15
        )
        keys = [s.key for s in org_sources(org_a, create=False)]
        assert keys == [key for key, _label in DEFAULT_SOURCES] + ["property portal"]
        assert LeadSource.objects.filter(org=org_a).count() == 1

    def test_a_key_is_unique_per_org(self, org_a):
        org_sources(org_a)
        with pytest.raises(IntegrityError), transaction.atomic():
            LeadSource.objects.create(org=org_a, key="call", label="Again")


# ---------------------------------------------------------------------------
# Intakes, their events, and the mailbox fields
# ---------------------------------------------------------------------------


class TestIntakeTables:
    def _intake(self, org, **fields):
        return LeadIntake.objects.create(
            org=org, name="Ads", key="k" * 40, mapping=[], **fields
        )

    def test_an_intake_holds_its_settings(self, org_a, admin_profile):
        tag = Tags.objects.create(name="Ads", org=org_a)
        intake = self._intake(
            org_a,
            preset="google_ads",
            default_source="google ads",
            source_detail="Spring",
            assignee=admin_profile,
        )
        intake.tags.add(tag)
        intake.refresh_from_db()
        assert intake.preset == "google_ads"
        assert intake.is_active is True
        assert intake.previous_key == ""
        assert intake.previous_key_expires_at is None
        assert intake.last_received_at is None
        assert intake.last_error == ""
        assert list(intake.tags.all()) == [tag]

    def test_a_tag_used_only_on_an_intake_is_in_use(self, admin_client, org_a):
        tag = Tags.objects.create(name="Ads", org=org_a)
        self._intake(org_a).tags.add(tag)
        body = admin_client.get("/api/tags/").data
        row = next(r for r in body["tags"] if str(r["id"]) == str(tag.id))
        assert row["usage"]["lead_intakes"] == 1
        assert body["totals"]["unused"] == 0

    def test_preset_defaults_to_generic(self, org_a):
        assert self._intake(org_a).preset == "generic"

    def test_removing_the_assignee_keeps_the_intake(self, org_a, admin_profile):
        intake = self._intake(org_a, assignee=admin_profile)
        admin_profile.delete()
        intake.refresh_from_db()
        assert intake.assignee is None

    def test_events_go_with_their_intake_and_outlive_their_lead(self, org_a):
        intake = self._intake(org_a)
        lead = _lead(org_a)
        kept = LeadIntakeEvent.objects.create(
            org=org_a, intake=intake, result="created", lead=lead, payload={"a": 1}
        )
        lead.delete()
        kept.refresh_from_db()
        assert kept.lead is None
        assert kept.received_at is not None
        intake.delete()
        assert not LeadIntakeEvent.objects.filter(pk=kept.pk).exists()

    def test_a_merge_moves_the_losers_events_to_the_keeper(self, org_a):
        intake = self._intake(org_a)
        keeper = _lead(org_a, email="a@example.com")
        loser = Lead.objects.create(org=org_a, first_name="Bo", email="b@example.com")
        event = LeadIntakeEvent.objects.create(
            org=org_a, intake=intake, result="created", lead=loser
        )
        merge_records(keeper, loser)
        event.refresh_from_db()
        assert event.lead_id == keeper.id

    def test_a_mailbox_creates_tickets_by_default(self, org_a):
        mailbox = InboundMailbox.objects.create(org=org_a, address="in@example.com")
        mailbox.refresh_from_db()
        assert mailbox.creates == "tickets"
        assert mailbox.lead_source == "email"
        assert mailbox.lead_source_detail == ""
        assert mailbox.is_generated is False

    def test_a_generated_address_is_unique_across_orgs(self, org_a, org_b):
        InboundMailbox.objects.create(
            org=org_a, address="acme-x1y2z3@in.example.com", is_generated=True
        )
        with rls_org(org_b):
            with pytest.raises(IntegrityError), transaction.atomic():
                InboundMailbox.objects.create(
                    org=org_b, address="acme-x1y2z3@in.example.com", is_generated=True
                )

    def test_a_typed_address_may_repeat_across_orgs(self, org_a, org_b):
        InboundMailbox.objects.create(org=org_a, address="sales@example.com")
        with rls_org(org_b):
            InboundMailbox.objects.create(org=org_b, address="sales@example.com")


# ---------------------------------------------------------------------------
# Merging keeps paired fields together
# ---------------------------------------------------------------------------


class TestMergePairs:
    def test_a_keeper_with_no_external_id_takes_the_losers_pair(self, org_a):
        keeper = _lead(org_a, email="a@example.com")
        loser = Lead.objects.create(
            org=org_a,
            first_name="Bo",
            email="b@example.com",
            external_source="intake:1",
            external_id="abc",
        )
        merge_records(keeper, loser)
        keeper.refresh_from_db()
        assert (keeper.external_source, keeper.external_id) == ("intake:1", "abc")

    def test_a_keeper_with_a_source_keeps_its_own_detail_blank(self, org_a):
        keeper = _lead(org_a, email="a@example.com", source="call")
        loser = Lead.objects.create(
            org=org_a,
            first_name="Bo",
            email="b@example.com",
            source="web form",
            source_detail="Zillow",
            source_ref="L-1",
        )
        merge_records(keeper, loser)
        keeper.refresh_from_db()
        assert (keeper.source, keeper.source_detail, keeper.source_ref) == (
            "call",
            "",
            "",
        )


# ---------------------------------------------------------------------------
# A web form's source is a key from the org's list
# ---------------------------------------------------------------------------


class TestWebFormSource:
    URL = "/api/webforms/"

    def test_a_new_form_gets_the_web_form_source(self, admin_client):
        response = admin_client.post(self.URL, {"name": "Contact"}, format="json")
        assert response.status_code == 201
        assert response.json()["lead_source"] == "web form"

    def test_any_active_source_is_accepted(self, admin_client):
        response = admin_client.post(
            self.URL, {"name": "Contact", "lead_source": "google ads"}, format="json"
        )
        assert response.status_code == 201
        assert WebForm.objects.get().lead_source == "google ads"

    def test_an_unknown_source_is_refused(self, admin_client):
        response = admin_client.post(
            self.URL, {"name": "Contact", "lead_source": "compaign"}, format="json"
        )
        assert response.status_code == 400
        assert not WebForm.objects.exists()

    def test_another_orgs_source_is_refused(self, admin_client, org_b):
        with rls_org(org_b):
            LeadSource.objects.create(org=org_b, key="their fair", label="Fair")
        response = admin_client.post(
            self.URL, {"name": "Contact", "lead_source": "their fair"}, format="json"
        )
        assert response.status_code == 400

    def test_a_retired_source_cannot_be_picked(self, admin_client, org_a):
        org_sources(org_a)
        LeadSource.objects.filter(org=org_a, key="partner").update(is_active=False)
        response = admin_client.post(
            self.URL, {"name": "Contact", "lead_source": "partner"}, format="json"
        )
        assert response.status_code == 400

    def test_a_form_keeps_its_stored_retired_source(self, admin_client, org_a):
        form = WebForm.objects.create(name="Contact", org=org_a, lead_source="partner")
        org_sources(org_a)
        LeadSource.objects.filter(org=org_a, key="partner").update(is_active=False)
        response = admin_client.put(
            f"{self.URL}{form.id}/",
            {"name": "Renamed", "lead_source": "partner"},
            format="json",
        )
        assert response.status_code == 200
        form.refresh_from_db()
        assert (form.name, form.lead_source) == ("Renamed", "partner")


# ---------------------------------------------------------------------------
# Data migrations
# ---------------------------------------------------------------------------


LEADS_DATA = "leads.migrations.0021_lead_source_campaign_and_phone_e164"
CONTACTS_DATA = "contacts.migrations.0015_backfill_contact_phone_e164"
DEALS_DATA = "opportunity.migrations.0024_map_deal_lead_sources"
WEBFORMS_MIGRATION = "webforms.migrations.0005_webform_lead_source_key"
RULES_DATA = "automation.migrations.0002_rule_lead_source_keys"
SAVED_VIEWS_DATA = "common.migrations.0058_saved_view_lead_source_keys"


class TestDataMigrations:
    def test_a_lead_stored_as_compaign_reads_campaign(self, org_a):
        lead = _lead(org_a)
        other = Lead.objects.create(org=org_a, first_name="Bo", source="partner")
        Lead.objects.filter(pk=lead.pk).update(source="compaign")
        _run(LEADS_DATA, "map_lead_sources")
        lead.refresh_from_db()
        other.refresh_from_db()
        assert lead.source == "campaign"
        assert other.source == "partner"

    @pytest.mark.parametrize(
        "old, new",
        [
            ("Website", "web form"),
            ("WEB", "web form"),
            ("Partner", "partner"),
            ("Referral", "referral"),
            ("  Other ", "other"),
            ("COMPAIGN", "campaign"),
            ("Google ads", "google ads"),
            ("Existing Customer", "existing customer"),
            # Free text is kept, never guessed at.
            ("Trade Show", "Trade Show"),
            ("PARTNER_REFERRAL", "PARTNER_REFERRAL"),
            ("None", "None"),
        ],
    )
    def test_lead_sources_match_without_case_or_spaces(self, org_a, old, new):
        lead = _lead(org_a)
        Lead.objects.filter(pk=lead.pk).update(source=old)
        _run(LEADS_DATA, "map_lead_sources")
        lead.refresh_from_db()
        assert lead.source == new

    def test_the_lead_source_rewrite_is_idempotent(self, org_a):
        lead = _lead(org_a)
        Lead.objects.filter(pk=lead.pk).update(source="Website")
        _run(LEADS_DATA, "map_lead_sources")
        _run(LEADS_DATA, "map_lead_sources")
        lead.refresh_from_db()
        assert lead.source == "web form"

    def test_a_web_form_stored_as_compaign_reads_campaign(self, org_a):
        form = WebForm.objects.create(name="Contact us", org=org_a)
        WebForm.objects.filter(pk=form.pk).update(lead_source="compaign")
        _run(WEBFORMS_MIGRATION, "rename_compaign_to_campaign")
        form.refresh_from_db()
        assert form.lead_source == "campaign"

    def test_the_lead_backfill_fills_phone_e164(self, org_a):
        lead = _lead(_us(org_a), phone="(555) 123-4567")
        blank = _lead(org_a, phone="")
        Lead.objects.filter(pk=lead.pk).update(phone_e164="")
        _run(LEADS_DATA, "backfill_lead_phone_e164")
        lead.refresh_from_db()
        blank.refresh_from_db()
        assert lead.phone_e164 == "+15551234567"
        assert blank.phone_e164 == ""

    def test_the_lead_backfill_runs_in_batches(self, org_a, monkeypatch):
        module = importlib.import_module(LEADS_DATA)
        monkeypatch.setattr(module, "BATCH_SIZE", 2)
        leads = [_lead(_us(org_a), phone=f"555-123-456{i}") for i in range(5)]
        Lead.objects.filter(org=org_a).update(phone_e164="")
        module.backfill_lead_phone_e164(
            global_apps, SimpleNamespace(connection=connection)
        )
        assert sorted(
            Lead.objects.filter(pk__in=[x.pk for x in leads]).values_list(
                "phone_e164", flat=True
            )
        ) == [f"+1555123456{i}" for i in range(5)]

    def test_the_contact_backfill_fills_phone_e164(self, org_a):
        contact = Contact.objects.create(
            org=_us(org_a), first_name="Ada", last_name="L", phone="555 123 4567"
        )
        Contact.objects.filter(pk=contact.pk).update(phone_e164="")
        _run(CONTACTS_DATA, "backfill_contact_phone_e164")
        contact.refresh_from_db()
        assert contact.phone_e164 == "+15551234567"

    @pytest.mark.parametrize(
        "old, new",
        [
            ("NONE", ""),
            ("", ""),
            ("CALL", "call"),
            ("EMAIL", "email"),
            ("EXISTING CUSTOMER", "existing customer"),
            ("PARTNER", "partner"),
            ("PUBLIC RELATIONS", "public relations"),
            ("CAMPAIGN", "campaign"),
            ("WEBSITE", "web form"),
            ("OTHER", "other"),
            # Conversion copied the lead's own value, misspelling included.
            ("compaign", "campaign"),
            ("partner", "partner"),
            # Case and surrounding spaces do not matter.
            ("Website", "web form"),
            ("WEB", "web form"),
            ("Partner", "partner"),
            ("Referral", "referral"),
            ("Other ", "other"),
            ("none", ""),
            ("Walk-In", "walk-in"),
            # Free text is kept exactly as stored.
            ("Trade Show", "Trade Show"),
            ("PARTNER_REFERRAL", "PARTNER_REFERRAL"),
            ("Email Campaign", "Email Campaign"),
            ("Cold Call", "Cold Call"),
        ],
    )
    def test_deal_sources_map_to_lead_source_keys(self, org_a, old, new):
        deal = Opportunity.objects.create(org=org_a, name="Deal")
        Opportunity.objects.filter(pk=deal.pk).update(lead_source=old)
        _run(DEALS_DATA, "map_deal_lead_sources")
        deal.refresh_from_db()
        assert deal.lead_source == new

    def test_the_deal_source_rewrite_is_idempotent(self, org_a):
        deal = Opportunity.objects.create(org=org_a, name="Deal")
        Opportunity.objects.filter(pk=deal.pk).update(lead_source="WEB")
        _run(DEALS_DATA, "map_deal_lead_sources")
        _run(DEALS_DATA, "map_deal_lead_sources")
        deal.refresh_from_db()
        assert deal.lead_source == "web form"

    def test_a_deal_with_no_source_stays_empty(self, org_a):
        deal = Opportunity.objects.create(org=org_a, name="Deal")
        _run(DEALS_DATA, "map_deal_lead_sources")
        deal.refresh_from_db()
        assert deal.lead_source in (None, "")

    def test_saved_views_follow_the_new_keys(self, org_a, admin_profile):
        def view(module, name, filters):
            return SavedView.objects.create(
                org=org_a,
                profile=admin_profile,
                module=module,
                name=name,
                filters=filters,
            )

        leads = view(
            "leads", "Campaigns", {"source": ["compaign", "partner", "Referral"]}
        )
        single = view("leads", "One", {"source": "compaign", "city": ["compaign"]})
        deals = view(
            "opportunities",
            "Web",
            {
                "lead_source": [
                    "WEBSITE",
                    "Website",
                    "WEB",
                    "CALL",
                    "NONE",
                    "Trade Show",
                ]
            },
        )
        # Another list's `source` parameter is not a lead source.
        other = view("contacts", "Untouched", {"city": ["CALL"]})

        _run(SAVED_VIEWS_DATA, "map_saved_view_sources")

        for v in (leads, single, deals, other):
            v.refresh_from_db()
        assert leads.filters == {"source": ["campaign", "partner", "referral"]}
        assert single.filters == {"source": "campaign", "city": ["compaign"]}
        assert deals.filters == {
            "lead_source": [
                "web form",
                "web form",
                "web form",
                "call",
                "NONE",
                "Trade Show",
            ]
        }
        assert other.filters == {"city": ["CALL"]}

    def test_automation_rules_follow_the_new_keys(self, org_a):
        lead_rule = AutomationRule.objects.create(
            org=org_a,
            name="Leads",
            object_key="lead",
            trigger={"event": "updated", "field": "source", "to": "compaign"},
            conditions=[
                {
                    "field": "source",
                    "op": "in",
                    "value": ["compaign", "partner", "Trade Show"],
                },
                {"field": "city", "op": "eq", "value": "compaign"},
            ],
            actions=[
                {
                    "type": "set_field",
                    "target": "record",
                    "field": "source",
                    "value": "compaign",
                },
                {"type": "notify", "to": "admins", "message": "compaign"},
            ],
        )
        deal_rule = AutomationRule.objects.create(
            org=org_a,
            name="Deals",
            object_key="deal",
            trigger={"event": "created"},
            conditions=[{"field": "lead_source", "op": "eq", "value": "WEBSITE"}],
            actions=[
                {
                    "type": "set_field",
                    "target": "record",
                    "field": "lead_source",
                    "value": "CALL",
                }
            ],
        )
        _run(RULES_DATA, "map_rule_source_values")
        lead_rule.refresh_from_db()
        deal_rule.refresh_from_db()
        assert lead_rule.trigger["to"] == "campaign"
        assert lead_rule.conditions[0]["value"] == [
            "campaign",
            "partner",
            "Trade Show",
        ]
        assert lead_rule.conditions[1]["value"] == "compaign"
        assert lead_rule.actions[0]["value"] == "campaign"
        assert lead_rule.actions[1]["message"] == "compaign"
        assert deal_rule.conditions[0]["value"] == "web form"
        assert deal_rule.actions[0]["value"] == "call"
        assert deal_rule.trigger == {"event": "created"}


# ---------------------------------------------------------------------------
# Duplicate detection by E.164
# ---------------------------------------------------------------------------


def _ids(found):
    return {record.id for record, _reasons in found}


class TestDuplicatesByE164:
    def test_international_input_matches_a_local_lead_in_a_us_org(
        self, org_a, admin_profile
    ):
        lead = _lead(_us(org_a), phone="(555) 123-4567")
        found = find_duplicates(
            visible_leads_qs(admin_profile), {"phone": "+1 555 123 4567"}, region="US"
        )
        assert _ids(found) == {lead.id}
        assert found[0][1] == ["phone"]

    def test_a_row_with_no_e164_still_matches_by_its_last_ten_digits(
        self, org_a, admin_profile
    ):
        lead = _lead(_us(org_a), phone="(555) 123-4567")
        Lead.objects.filter(pk=lead.pk).update(phone_e164="")
        found = find_duplicates(
            visible_leads_qs(admin_profile), {"phone": "+1 555 123 4567"}, region="US"
        )
        assert _ids(found) == {lead.id}
        assert found[0][1] == ["phone"]

    def test_local_numbers_in_an_org_with_no_country_match_as_before(
        self, org_a, admin_profile
    ):
        lead = _lead(org_a, phone="555-123-4567")
        found = find_duplicates(
            visible_leads_qs(admin_profile), {"phone": "(555) 123-4567"}, region=None
        )
        assert _ids(found) == {lead.id}

    def test_e164_matches_a_short_number_the_digit_rule_cannot(
        self, org_a, admin_profile
    ):
        org_a.default_country = "SG"
        org_a.save(update_fields=["default_country"])
        contact = Contact.objects.create(
            org=org_a, first_name="Ada", last_name="L", phone="6123 4567"
        )
        found = find_duplicates(
            visible_contacts_qs(admin_profile), {"phone": "+65 6123 4567"}, region="SG"
        )
        assert _ids(found) == {contact.id}
        assert found[0][1] == ["phone"]

    def test_differing_e164_values_still_match_by_their_last_ten_digits(
        self, org_a, admin_profile
    ):
        """Detection only suggests, so E.164 adds matches and drops none."""
        lead = _lead(_us(org_a), phone="98765 43210")
        lead.refresh_from_db()
        assert lead.phone_e164 == "+19876543210"
        found = find_duplicates(
            visible_leads_qs(admin_profile), {"phone": "+91 98765 43210"}, region="US"
        )
        assert _ids(found) == {lead.id}
        assert found[0][1] == ["phone"]

    def test_the_check_endpoint_uses_the_orgs_country(
        self, org_a, admin_profile, admin_client
    ):
        org_a.default_country = "SG"
        org_a.save(update_fields=["default_country"])
        contact = Contact.objects.create(
            org=org_a, first_name="Ada", last_name="L", phone="+65 6123 4567"
        )
        response = admin_client.post(
            "/api/contacts/duplicates/", {"phone": "6123 4567"}, format="json"
        )
        assert response.status_code == 200
        assert [hit["id"] for hit in response.json()["duplicates"]] == [str(contact.id)]


# ---------------------------------------------------------------------------
# PostgreSQL: row-level security on the new tables and the backfill under it
# ---------------------------------------------------------------------------


@pytest.mark.postgres_only
def test_the_new_tables_hide_another_orgs_rows(org_a, org_b):
    """Only meaningful under the CI role that RLS binds."""
    if connection.vendor != "postgresql":
        pytest.skip("RLS requires PostgreSQL")
    org_sources(org_a)
    mine = LeadIntake.objects.create(org=org_a, name="Mine", key="a" * 40)
    LeadIntakeEvent.objects.create(org=org_a, intake=mine, result="test")
    with rls_org(org_b):
        org_sources(org_b)
        theirs = LeadIntake.objects.create(org=org_b, name="Theirs", key="b" * 40)
        LeadIntakeEvent.objects.create(org=org_b, intake=theirs, result="test")

    assert set(LeadSource.objects.values_list("org_id", flat=True)) == {org_a.id}
    assert list(LeadIntake.objects.all()) == [mine]
    assert set(LeadIntakeEvent.objects.values_list("org_id", flat=True)) == {org_a.id}


@pytest.mark.postgres_only
def test_the_backfills_reach_every_org_with_no_context_set(org_a, org_b):
    """A migration runs with `app.current_org` empty, under which FORCE RLS
    hides every row. The org loop is what makes the backfill do anything."""
    if connection.vendor != "postgresql":
        pytest.skip("RLS requires PostgreSQL")
    _us(org_a)
    _us(org_b)
    mine = _lead(org_a, phone="555-123-4567", source="partner")
    Lead.objects.filter(pk=mine.pk).update(phone_e164="", source="compaign")
    with rls_org(org_b):
        theirs = _lead(org_b, phone="555-987-6543")
        Lead.objects.filter(pk=theirs.pk).update(phone_e164="")
        deal = Opportunity.objects.create(org=org_b, name="Deal")
        Opportunity.objects.filter(pk=deal.pk).update(lead_source="WEBSITE")
    clear_rls_context()

    _run(LEADS_DATA, "map_lead_sources")
    _run(LEADS_DATA, "backfill_lead_phone_e164")
    _run(DEALS_DATA, "map_deal_lead_sources")

    set_rls_context(org_a)
    mine.refresh_from_db()
    assert (mine.phone_e164, mine.source) == ("+15551234567", "campaign")
    with rls_org(org_b):
        theirs.refresh_from_db()
        deal.refresh_from_db()
        assert theirs.phone_e164 == "+15559876543"
        assert deal.lead_source == "web form"
