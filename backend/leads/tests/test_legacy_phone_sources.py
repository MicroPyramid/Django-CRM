"""Phone builds before the app header cannot show a source they were never
shipped, so they must not wipe one. Browsers and current phones get no such
courtesy."""

import pytest

from leads.models import Lead, LeadSource
from leads.sources import org_sources
from opportunity.models import Opportunity

LEGACY = {"HTTP_USER_AGENT": "Dart/3.4 (dart:io)"}
CURRENT_PHONE = {
    "HTTP_USER_AGENT": "Dart/3.4 (dart:io)",
    "HTTP_X_BOTTLECRM_APP": "1.13.0",
}
WEB = {"HTTP_USER_AGENT": "Mozilla/5.0"}

pytestmark = pytest.mark.django_db


def _lead(org, source):
    return Lead.objects.create(org=org, first_name="Ada", last_name="L", source=source)


def _save(client, lead, body, headers, verb="put"):
    payload = {"first_name": "Ada", "last_name": "L", **body}
    return getattr(client, verb)(
        f"/api/leads/{lead.id}/", payload, format="json", **headers
    )


class TestLead:
    def test_other_over_google_ads_leaves_google_ads(self, admin_client, org_a):
        lead = _lead(org_a, "google ads")
        response = _save(admin_client, lead, {"source": "other"}, LEGACY)
        assert response.status_code == 200, response.content
        lead.refresh_from_db()
        assert lead.source == "google ads"

    def test_the_same_edit_from_the_web_stores_other(self, admin_client, org_a):
        lead = _lead(org_a, "google ads")
        assert _save(admin_client, lead, {"source": "other"}, WEB).status_code == 200
        lead.refresh_from_db()
        assert lead.source == "other"

    def test_the_same_edit_from_a_current_phone_stores_other(self, admin_client, org_a):
        lead = _lead(org_a, "google ads")
        assert (
            _save(admin_client, lead, {"source": "other"}, CURRENT_PHONE).status_code
            == 200
        )
        lead.refresh_from_db()
        assert lead.source == "other"

    def test_the_old_misspelling_is_stored_as_campaign(self, admin_client, org_a):
        lead = _lead(org_a, None)
        assert (
            _save(admin_client, lead, {"source": "compaign"}, LEGACY).status_code == 200
        )
        lead.refresh_from_db()
        assert lead.source == "campaign"

    def test_the_misspelling_from_the_web_is_refused(self, admin_client, org_a):
        lead = _lead(org_a, None)
        assert _save(admin_client, lead, {"source": "compaign"}, WEB).status_code == 400

    def test_a_real_change_among_the_old_keys_is_honoured(self, admin_client, org_a):
        lead = _lead(org_a, "call")
        assert _save(admin_client, lead, {"source": "other"}, LEGACY).status_code == 200
        lead.refresh_from_db()
        assert lead.source == "other"

    def test_other_over_a_stored_campaign_is_kept(self, admin_client, org_a):
        # The old lead picker only knows `compaign`, so it reads `campaign`
        # as Other and saves "other".
        lead = _lead(org_a, "campaign")
        assert _save(admin_client, lead, {"source": "other"}, LEGACY).status_code == 200
        lead.refresh_from_db()
        assert lead.source == "campaign"

    def test_a_stored_key_the_old_picker_lacks_survives_a_blank(
        self, admin_client, org_a
    ):
        lead = _lead(org_a, "referral")
        response = _save(admin_client, lead, {"source": ""}, LEGACY, verb="patch")
        assert response.status_code == 200
        lead.refresh_from_db()
        assert lead.source == "referral"

    def test_a_blank_from_the_web_clears_the_source(self, admin_client, org_a):
        lead = _lead(org_a, "referral")
        response = _save(admin_client, lead, {"source": ""}, WEB, verb="patch")
        assert response.status_code == 200
        lead.refresh_from_db()
        assert not lead.source

    def test_other_over_a_retired_key_leaves_it(self, admin_client, org_a):
        lead = _lead(org_a, "google ads")
        org_sources(org_a)
        LeadSource.objects.filter(org=org_a, key="google ads").update(is_active=False)
        assert _save(admin_client, lead, {"source": "other"}, LEGACY).status_code == 200
        lead.refresh_from_db()
        assert lead.source == "google ads"

    def test_a_legacy_phone_still_cannot_send_a_stranger(self, admin_client, org_a):
        lead = _lead(org_a, "call")
        assert _save(admin_client, lead, {"source": "zzz"}, LEGACY).status_code == 400

    def test_creating_from_a_legacy_phone_with_the_old_values(self, admin_client):
        response = admin_client.post(
            "/api/leads/",
            {"first_name": "Ada", "last_name": "L", "source": "compaign"},
            format="json",
            **LEGACY,
        )
        assert response.status_code in (200, 201)
        assert Lead.objects.get().source == "campaign"


class TestDeal:
    def _deal(self, org, source):
        return Opportunity.objects.create(
            org=org, name="D", closed_on="2026-12-01", lead_source=source
        )

    def _save(self, client, deal, body, headers):
        return client.patch(
            f"/api/opportunities/{deal.id}/", body, format="json", **headers
        )

    def test_other_over_a_new_key_leaves_it(self, admin_client, org_a):
        deal = self._deal(org_a, "meta ads")
        response = self._save(admin_client, deal, {"lead_source": "OTHER"}, LEGACY)
        assert response.status_code == 200, response.content
        deal.refresh_from_db()
        assert deal.lead_source == "meta ads"

    def test_the_same_edit_from_the_web_is_refused_for_uppercase(
        self, admin_client, org_a
    ):
        deal = self._deal(org_a, "meta ads")
        assert (
            self._save(admin_client, deal, {"lead_source": "OTHER"}, WEB).status_code
            == 400
        )
        assert (
            self._save(admin_client, deal, {"lead_source": "other"}, WEB).status_code
            == 200
        )
        deal.refresh_from_db()
        assert deal.lead_source == "other"

    def test_uppercase_values_are_translated_for_a_legacy_phone(
        self, admin_client, org_a
    ):
        deal = self._deal(org_a, "call")
        response = self._save(admin_client, deal, {"lead_source": "WEBSITE"}, LEGACY)
        assert response.status_code == 200
        deal.refresh_from_db()
        assert deal.lead_source == "web form"

    def test_a_current_phone_is_not_translated(self, admin_client, org_a):
        deal = self._deal(org_a, "call")
        assert (
            self._save(
                admin_client, deal, {"lead_source": "WEBSITE"}, CURRENT_PHONE
            ).status_code
            == 400
        )

    def test_none_over_a_stored_web_form_is_kept(self, admin_client, org_a):
        # The old deal picker has no `web form`, reads it as None and sends
        # "NONE", which would otherwise clear it.
        deal = self._deal(org_a, "web form")
        response = self._save(admin_client, deal, {"lead_source": "NONE"}, LEGACY)
        assert response.status_code == 200
        deal.refresh_from_db()
        assert deal.lead_source == "web form"

    def test_other_over_a_stored_campaign_deal_is_honoured(self, admin_client, org_a):
        # The old deal picker reads `campaign` fine, so "OTHER" is a real choice.
        deal = self._deal(org_a, "campaign")
        response = self._save(admin_client, deal, {"lead_source": "OTHER"}, LEGACY)
        assert response.status_code == 200
        deal.refresh_from_db()
        assert deal.lead_source == "other"

    def test_the_web_clears_a_deal_source_with_a_blank(self, admin_client, org_a):
        deal = self._deal(org_a, "web form")
        response = self._save(admin_client, deal, {"lead_source": ""}, WEB)
        assert response.status_code == 200
        deal.refresh_from_db()
        assert not deal.lead_source
