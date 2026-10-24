"""Lead sources: the endpoints, validation on leads, contacts and deals,
conversion, packs and CSV import."""

import csv
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import Account
from common.client_version import is_legacy_phone
from common.packs.applier import apply_pack
from common.packs.loader import get_pack
from common.testing import rls_org
from contacts.models import Contact
from leads.models import Lead, LeadSource
from leads.sources import DEFAULT_SOURCES, org_sources
from opportunity.models import Opportunity

SOURCES = "/api/leads/sources/"

pytestmark = pytest.mark.django_db


def _retire(org, key):
    org_sources(org)
    LeadSource.objects.filter(org=org, key=key).update(is_active=False)


def _source(org, key):
    return LeadSource.objects.get(org=org, key=key)


class TestListing:
    def test_a_member_lists_the_fifteen_defaults_in_order(self, user_client):
        response = user_client.get(SOURCES)
        assert response.status_code == 200
        rows = response.json()["sources"]
        assert [r["key"] for r in rows] == [k for k, _ in DEFAULT_SOURCES]
        assert len(rows) == 15
        assert set(rows[0]) == {"id", "key", "label", "is_active", "order"}
        assert [r["order"] for r in rows] == list(range(15))

    def test_retired_sources_are_listed(self, user_client, org_a):
        _retire(org_a, "partner")
        rows = user_client.get(SOURCES).json()["sources"]
        partner = next(r for r in rows if r["key"] == "partner")
        assert partner["is_active"] is False

    def test_an_unauthenticated_caller_is_refused(self, unauthenticated_client):
        assert unauthenticated_client.get(SOURCES).status_code in (401, 403)

    def test_another_orgs_sources_are_not_listed(self, admin_client, org_b):
        with rls_org(org_b):
            LeadSource.objects.create(org=org_b, key="their fair", label="Fair")
        keys = [r["key"] for r in admin_client.get(SOURCES).json()["sources"]]
        assert "their fair" not in keys

    def test_listing_works_with_leads_switched_off(self, user_client, org_a):
        from common.testing import set_modules_off

        set_modules_off(org_a, "leads")
        assert user_client.get(SOURCES).status_code == 200


class TestAdminWrites:
    def test_a_member_cannot_create(self, user_client, org_a):
        response = user_client.post(SOURCES, {"label": "Spring fair"}, format="json")
        assert response.status_code == 403
        assert not LeadSource.objects.filter(org=org_a, key="spring fair").exists()

    def test_a_member_cannot_patch_or_order(self, user_client, org_a):
        org_sources(org_a)
        source = _source(org_a, "call")
        assert (
            user_client.patch(
                f"{SOURCES}{source.id}/", {"is_active": False}, format="json"
            ).status_code
            == 403
        )
        assert (
            user_client.post(
                f"{SOURCES}order/", {"keys": ["email"]}, format="json"
            ).status_code
            == 403
        )

    def test_an_admin_creates_a_source_with_a_derived_key(self, admin_client, org_a):
        response = admin_client.post(SOURCES, {"label": "Spring fair"}, format="json")
        assert response.status_code == 201
        body = response.json()
        assert body["key"] == "spring fair"
        assert body["label"] == "Spring fair"
        assert body["is_active"] is True
        assert body["order"] == 15
        assert _source(org_a, "spring fair").label == "Spring fair"

    def test_the_same_label_twice_is_refused(self, admin_client):
        admin_client.post(SOURCES, {"label": "Spring fair"}, format="json")
        again = admin_client.post(SOURCES, {"label": "  spring   FAIR "}, format="json")
        assert again.status_code == 400

    def test_a_label_that_clashes_with_a_default_is_refused(self, admin_client):
        assert (
            admin_client.post(
                SOURCES, {"label": "Google Ads"}, format="json"
            ).status_code
            == 400
        )

    @pytest.mark.parametrize(
        "payload", [{}, {"label": ""}, {"label": "   "}, {"label": "x" * 65}]
    )
    def test_a_bad_label_is_refused(self, admin_client, payload):
        assert admin_client.post(SOURCES, payload, format="json").status_code == 400

    def test_two_orgs_may_use_the_same_label(self, admin_client, org_b):
        with rls_org(org_b):
            LeadSource.objects.create(org=org_b, key="spring fair", label="Spring fair")
        assert (
            admin_client.post(
                SOURCES, {"label": "Spring fair"}, format="json"
            ).status_code
            == 201
        )

    def test_patch_retires_renames_and_keeps_the_key(self, admin_client, org_a):
        org_sources(org_a)
        source = _source(org_a, "partner")
        response = admin_client.patch(
            f"{SOURCES}{source.id}/",
            {"is_active": False, "label": "Channel partner"},
            format="json",
        )
        assert response.status_code == 200
        source.refresh_from_db()
        assert (source.key, source.label, source.is_active) == (
            "partner",
            "Channel partner",
            False,
        )

    def test_patch_ignores_a_key_in_the_body(self, admin_client, org_a):
        org_sources(org_a)
        source = _source(org_a, "partner")
        response = admin_client.patch(
            f"{SOURCES}{source.id}/", {"key": "hijack", "label": "P"}, format="json"
        )
        assert response.status_code == 200
        source.refresh_from_db()
        assert (source.key, source.label) == ("partner", "P")

    def test_patch_refuses_a_label_another_source_uses(self, admin_client, org_a):
        org_sources(org_a)
        source = _source(org_a, "partner")
        for label in ("Call", "call", "  GOOGLE   ads "):
            response = admin_client.patch(
                f"{SOURCES}{source.id}/", {"label": label}, format="json"
            )
            assert response.status_code == 400, label
        source.refresh_from_db()
        assert source.label == "Partner"

    def test_patch_may_resend_its_own_label(self, admin_client, org_a):
        org_sources(org_a)
        source = _source(org_a, "partner")
        response = admin_client.patch(
            f"{SOURCES}{source.id}/", {"label": "partner"}, format="json"
        )
        assert response.status_code == 200

    def test_another_orgs_source_id_is_404(self, admin_client, org_b):
        with rls_org(org_b):
            theirs = LeadSource.objects.create(org=org_b, key="x", label="X")
        response = admin_client.patch(
            f"{SOURCES}{theirs.id}/", {"is_active": False}, format="json"
        )
        assert response.status_code == 404
        theirs.refresh_from_db()
        assert theirs.is_active is True

    def test_order_sets_the_order_and_keeps_the_rest_after(self, admin_client, org_a):
        response = admin_client.post(
            f"{SOURCES}order/", {"keys": ["referral", "walk-in"]}, format="json"
        )
        assert response.status_code == 200
        keys = [r["key"] for r in response.json()["sources"]]
        assert keys[:3] == ["referral", "walk-in", "call"]
        assert len(keys) == 15
        assert _source(org_a, "referral").order == 0
        listed = [r["key"] for r in admin_client.get(SOURCES).json()["sources"]]
        assert listed == keys

    @pytest.mark.parametrize(
        "keys", [["nope"], ["call", "call"], [], "call", ["call", 3]]
    )
    def test_order_refuses_bad_keys(self, admin_client, keys):
        response = admin_client.post(f"{SOURCES}order/", {"keys": keys}, format="json")
        assert response.status_code == 400

    def test_order_cannot_name_another_orgs_key(self, admin_client, org_b):
        with rls_org(org_b):
            LeadSource.objects.create(org=org_b, key="their fair", label="Fair")
        response = admin_client.post(
            f"{SOURCES}order/", {"keys": ["their fair"]}, format="json"
        )
        assert response.status_code == 400


class TestLeadSourceValidation:
    URL = "/api/leads/"

    def _create(self, client, **extra):
        return client.post(
            self.URL,
            {"first_name": "Ada", "last_name": "L", **extra},
            format="json",
        )

    def test_an_active_source_is_accepted(self, admin_client):
        response = self._create(admin_client, source="google ads")
        assert response.status_code == 200 or response.status_code == 201
        assert Lead.objects.get().source == "google ads"

    def test_an_unknown_source_is_refused(self, admin_client):
        response = self._create(admin_client, source="made up")
        assert response.status_code == 400
        assert not Lead.objects.exists()

    def test_the_old_misspelling_is_refused_from_the_web(self, admin_client):
        assert self._create(admin_client, source="compaign").status_code == 400

    def test_a_label_is_not_a_key(self, admin_client):
        assert self._create(admin_client, source="Google Ads").status_code == 400

    def test_another_orgs_source_is_refused(self, admin_client, org_b):
        with rls_org(org_b):
            LeadSource.objects.create(org=org_b, key="their fair", label="Fair")
        assert self._create(admin_client, source="their fair").status_code == 400

    def test_a_retired_source_cannot_be_chosen(self, admin_client, org_a):
        _retire(org_a, "partner")
        assert self._create(admin_client, source="partner").status_code == 400

    def test_a_retired_source_stays_on_its_lead_and_saves_unchanged(
        self, admin_client, org_a
    ):
        lead = Lead.objects.create(
            org=org_a, first_name="Ada", last_name="L", source="partner"
        )
        _retire(org_a, "partner")
        response = admin_client.patch(
            f"{self.URL}{lead.id}/",
            {"source": "partner", "city": "Pune"},
            format="json",
        )
        assert response.status_code == 200
        lead.refresh_from_db()
        assert (lead.source, lead.city) == ("partner", "Pune")

    def test_a_blank_source_is_allowed(self, admin_client):
        assert self._create(admin_client, source="").status_code in (200, 201)

    def test_detail_and_reference_are_stored_and_returned(self, admin_client):
        response = self._create(
            admin_client,
            source="google ads",
            source_detail="Spring campaign",
            source_ref="gclid-123",
        )
        assert response.status_code in (200, 201)
        lead = Lead.objects.get()
        assert (lead.source_detail, lead.source_ref) == ("Spring campaign", "gclid-123")
        body = admin_client.get(f"{self.URL}{lead.id}/").json()["lead_obj"]
        assert body["source_detail"] == "Spring campaign"
        assert body["source_ref"] == "gclid-123"
        for name in (
            "phone_e164",
            "external_source",
            "external_id",
            "last_enquiry_at",
        ):
            assert name in body

    def test_detail_over_100_is_refused(self, admin_client):
        assert self._create(admin_client, source_detail="x" * 101).status_code == 400
        assert self._create(admin_client, source_detail="x" * 100).status_code in (
            200,
            201,
        )

    def test_reference_over_255_is_refused(self, admin_client):
        assert self._create(admin_client, source_ref="x" * 256).status_code == 400

    def test_server_set_fields_cannot_be_written(self, admin_client):
        self._create(
            admin_client,
            phone_e164="+1",
            external_source="a",
            external_id="b",
            last_enquiry_at="2026-01-01T00:00:00Z",
        )
        lead = Lead.objects.get()
        assert (lead.external_source, lead.external_id) == ("", "")
        assert lead.last_enquiry_at is None
        assert lead.phone_e164 == ""


LEGACY = {"HTTP_USER_AGENT": "Dart/3.4 (dart:io)"}


class TestIsLegacyPhone:
    class Req:
        def __init__(self, **meta):
            self.META = meta

    def test_dart_agent_without_the_header_is_legacy(self):
        assert is_legacy_phone(self.Req(HTTP_USER_AGENT="Dart/3.4 (dart:io)"))

    def test_the_app_header_makes_it_current(self):
        assert not is_legacy_phone(
            self.Req(HTTP_USER_AGENT="Dart/3.4", HTTP_X_BOTTLECRM_APP="1.13.0")
        )

    def test_a_browser_and_a_missing_agent_are_not_legacy(self):
        assert not is_legacy_phone(self.Req(HTTP_USER_AGENT="Mozilla/5.0"))
        assert not is_legacy_phone(self.Req())

    def test_the_agent_must_start_with_dart(self):
        assert not is_legacy_phone(self.Req(HTTP_USER_AGENT="curl Dart/3"))


class TestConversion:
    def test_source_detail_and_ref_reach_the_contact_and_the_deal(
        self, admin_client, org_a
    ):
        lead = Lead.objects.create(
            org=org_a,
            first_name="Ada",
            last_name="L",
            email="ada@example.com",
            company_name="Acme",
            opportunity_amount=100,
            source="google ads",
            source_detail="Spring",
            source_ref="gclid-1",
        )
        response = admin_client.patch(
            f"/api/leads/{lead.id}/", {"status": "converted"}, format="json"
        )
        assert response.status_code == 200, response.content
        contact = Contact.objects.get(org=org_a, email="ada@example.com")
        deal = Opportunity.objects.get(org=org_a)
        assert (contact.source, contact.source_detail, contact.source_ref) == (
            "google ads",
            "Spring",
            "gclid-1",
        )
        assert (deal.lead_source, deal.source_detail, deal.source_ref) == (
            "google ads",
            "Spring",
            "gclid-1",
        )
        assert Account.objects.filter(org=org_a).exists()

    def test_a_lead_with_no_source_converts(self, admin_client, org_a):
        lead = Lead.objects.create(
            org=org_a,
            first_name="Ada",
            last_name="L",
            email="ada@example.com",
            company_name="Acme",
            opportunity_amount=100,
        )
        response = admin_client.patch(
            f"/api/leads/{lead.id}/", {"status": "converted"}, format="json"
        )
        assert response.status_code == 200
        assert Contact.objects.get(org=org_a, email="ada@example.com").source == ""


class TestRetiredFromTheWeb:
    def test_an_existing_lead_cannot_be_moved_to_a_retired_source(
        self, admin_client, org_a
    ):
        lead = Lead.objects.create(
            org=org_a, first_name="Ada", last_name="L", source="call"
        )
        _retire(org_a, "partner")
        response = admin_client.patch(
            f"/api/leads/{lead.id}/", {"source": "partner"}, format="json"
        )
        assert response.status_code == 400
        lead.refresh_from_db()
        assert lead.source == "call"

    def test_an_existing_deal_cannot_be_moved_to_a_retired_source(
        self, admin_client, org_a
    ):
        deal = Opportunity.objects.create(
            org=org_a, name="D", closed_on="2026-12-01", lead_source="call"
        )
        _retire(org_a, "partner")
        response = admin_client.patch(
            f"/api/opportunities/{deal.id}/", {"lead_source": "partner"}, format="json"
        )
        assert response.status_code == 400
        deal.refresh_from_db()
        assert deal.lead_source == "call"

    def test_a_contact_keeps_its_retired_source_unchanged(self, admin_client, org_a):
        contact = Contact.objects.create(
            org=org_a, first_name="Bo", last_name="K", source="partner"
        )
        _retire(org_a, "partner")
        response = admin_client.patch(
            f"/api/contacts/{contact.id}/",
            {"source": "partner", "city": "Pune"},
            format="json",
        )
        assert response.status_code == 200, response.content
        contact.refresh_from_db()
        assert (contact.source, contact.city) == ("partner", "Pune")

    def test_a_contact_cannot_be_moved_to_a_retired_source(self, admin_client, org_a):
        contact = Contact.objects.create(
            org=org_a, first_name="Bo", last_name="K", source="call"
        )
        _retire(org_a, "partner")
        response = admin_client.patch(
            f"/api/contacts/{contact.id}/", {"source": "partner"}, format="json"
        )
        assert response.status_code == 400

    def test_contact_detail_and_reference_limits(self, admin_client):
        def post(**extra):
            return admin_client.post(
                "/api/contacts/",
                {"first_name": "Bo", "last_name": "K", **extra},
                format="json",
            )

        assert post(source_detail="x" * 101).status_code == 400
        assert post(source_ref="x" * 256).status_code == 400
        ok = post(source_detail="x" * 100, source_ref="y" * 255)
        assert ok.status_code in (200, 201), ok.content


class TestContactAndDealSerializers:
    def test_a_contact_carries_source_columns_and_phone_e164(self, admin_client, org_a):
        response = admin_client.post(
            "/api/contacts/",
            {
                "first_name": "Bo",
                "last_name": "K",
                "source": "referral",
                "source_detail": "Dana",
                "source_ref": "r-1",
            },
            format="json",
        )
        assert response.status_code in (200, 201), response.content
        contact = Contact.objects.get(org=org_a)
        assert contact.source == "referral"
        body = admin_client.get(f"/api/contacts/{contact.id}/").json()
        card = body.get("contact_obj", body)
        assert card["source"] == "referral"
        assert card["source_detail"] == "Dana"
        assert "phone_e164" in card

    def test_a_contact_with_an_unknown_source_is_refused(self, admin_client):
        response = admin_client.post(
            "/api/contacts/",
            {"first_name": "Bo", "last_name": "K", "source": "nope"},
            format="json",
        )
        assert response.status_code == 400

    def _deal(self, client, **extra):
        return client.post(
            "/api/opportunities/",
            {
                "name": "Big one",
                "closed_on": "2026-12-01",
                **extra,
            },
            format="json",
        )

    def test_a_deal_takes_a_key_and_detail(self, admin_client, org_a):
        response = self._deal(
            admin_client,
            lead_source="meta ads",
            source_detail="Reel",
            source_ref="ad-9",
        )
        assert response.status_code in (200, 201), response.content
        deal = Opportunity.objects.get(org=org_a)
        assert (deal.lead_source, deal.source_detail, deal.source_ref) == (
            "meta ads",
            "Reel",
            "ad-9",
        )
        body = admin_client.get(f"/api/opportunities/{deal.id}/").json()
        row = body.get("opportunity_obj", body)
        assert row["source_detail"] == "Reel"
        assert row["source_ref"] == "ad-9"

    def test_a_deal_with_an_unknown_source_is_refused(self, admin_client):
        assert self._deal(admin_client, lead_source="WEBSITE").status_code == 400
        assert self._deal(admin_client, lead_source="made up").status_code == 400

    def test_deal_detail_limits_match_the_lead(self, admin_client):
        assert self._deal(admin_client, source_detail="x" * 101).status_code == 400
        assert self._deal(admin_client, source_ref="x" * 256).status_code == 400

    def test_a_retired_deal_source_stays(self, admin_client, org_a):
        deal = Opportunity.objects.create(
            org=org_a, name="D", closed_on="2026-12-01", lead_source="partner"
        )
        _retire(org_a, "partner")
        response = admin_client.patch(
            f"/api/opportunities/{deal.id}/",
            {"lead_source": "partner", "description": "x"},
            format="json",
        )
        assert response.status_code == 200, response.content
        deal.refresh_from_db()
        assert deal.lead_source == "partner"


class TestPacks:
    def test_the_real_estate_pack_adds_property_portal(self, org_a, admin_profile):
        report = apply_pack(org_a, get_pack("real-estate"), admin_profile)
        source = _source(org_a, "property portal")
        assert source.label == "Property portal"
        assert source.order == 15
        assert {"type": "lead_source", "name": "Property portal"} in report["created"]
        assert report["failed"] == []

    def test_applying_twice_keeps_one(self, org_a, admin_profile):
        apply_pack(org_a, get_pack("real-estate"), admin_profile)
        again = apply_pack(org_a, get_pack("real-estate"), admin_profile)
        assert LeadSource.objects.filter(org=org_a, key="property portal").count() == 1
        assert {
            "type": "lead_source",
            "name": "Property portal",
            "reason": "already exists",
        } in again["skipped"]

    def test_a_retired_pack_source_is_left_retired(self, org_a, admin_profile):
        apply_pack(org_a, get_pack("real-estate"), admin_profile)
        LeadSource.objects.filter(org=org_a, key="property portal").update(
            is_active=False
        )
        apply_pack(org_a, get_pack("real-estate"), admin_profile)
        assert _source(org_a, "property portal").is_active is False

    def test_the_manifest_schema_checks_lead_sources(self):
        from common.packs.schema import PackValidationError, validate_manifest

        base = {"id": "x", "name": "X", "version": 1}
        for bad in (
            [{"key": "Upper", "label": "U"}],
            [{"key": "a"}],
            [{"key": "a", "label": "A", "extra": 1}],
            [{"key": "a", "label": "A"}, {"key": "a", "label": "B"}],
            "nope",
        ):
            with pytest.raises(PackValidationError):
                validate_manifest({**base, "lead_sources": bad})
        validate_manifest({**base, "lead_sources": [{"key": "a b", "label": "A B"}]})

    def test_a_sample_lead_may_use_a_pack_source_but_not_a_stranger(self):
        from common.packs.schema import PackValidationError, validate_manifest

        def pack(source, listed):
            return {
                "id": "x",
                "name": "X",
                "version": 1,
                "lead_sources": listed,
                "sample_dates_written_on": "2026-08-03",
                "sample_data": {"leads": [{"title": "T", "source": source}]},
            }

        listed = [{"key": "expo", "label": "Expo"}]
        validate_manifest(pack("expo", listed))
        validate_manifest(pack("google ads", []))
        with pytest.raises(PackValidationError):
            validate_manifest(pack("expo", []))


def _upload(rows):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["first_name", "last_name", "email", "source"])
    writer.writerows(rows)
    return SimpleUploadedFile("leads.csv", buf.getvalue().encode(), "text/csv")


class TestCsvImport:
    COMMIT = "/api/leads/import/commit/"

    def test_a_label_and_a_key_both_map(self, admin_client, org_a):
        response = admin_client.post(
            self.COMMIT,
            {
                "file": _upload(
                    [
                        ["Ada", "A", "a@example.com", "Google ads"],
                        ["Bo", "B", "b@example.com", "google ads"],
                        ["Cy", "C", "c@example.com", "LinkedIn Ads"],
                        ["Di", "D", "d@example.com", ""],
                    ]
                )
            },
            format="multipart",
        )
        assert response.status_code == 200, response.content
        got = {lead.first_name: lead.source for lead in Lead.objects.filter(org=org_a)}
        assert got["Ada"] == "google ads"
        assert got["Bo"] == "google ads"
        assert got["Cy"] == "linkedin ads"
        assert got["Di"] in (None, "")

    def test_an_unknown_source_is_a_row_error(self, admin_client, org_a):
        response = admin_client.post(
            self.COMMIT,
            {"file": _upload([["Ada", "A", "a@example.com", "Billboard"]])},
            format="multipart",
        )
        assert response.status_code == 400
        assert not Lead.objects.filter(org=org_a).exists()
        assert response.json()["errors"][0]["field"] == "source"

    def test_a_retired_source_is_not_mapped(self, admin_client, org_a):
        _retire(org_a, "partner")
        response = admin_client.post(
            self.COMMIT,
            {"file": _upload([["Ada", "A", "a@example.com", "Partner"]])},
            format="multipart",
        )
        assert response.status_code == 400
