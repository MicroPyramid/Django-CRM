"""Opportunities-side tests for custom fields: Opportunity create/update payloads,
list filter, and detail-page response shape.

Mirrors leads/tests/test_custom_fields.py.
"""

from __future__ import annotations

import pytest
from django.db import connection

from common.models import CustomFieldDefinition
from opportunity.models import Opportunity

pg_only = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="JSONField __contains lookup requires PostgreSQL",
)


OPPORTUNITIES_LIST_URL = "/api/opportunities/"


def _set_rls(org):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.current_org', %s, false)", [str(org.id)]
        )


def _make_tier_def(org, **overrides):
    defaults = {
        "target_model": "Opportunity",
        "key": "deal_tier",
        "label": "Deal Tier",
        "field_type": "dropdown",
        "options": [
            {"value": "strategic", "label": "Strategic"},
            {"value": "standard", "label": "Standard"},
        ],
        "is_required": False,
        "is_active": True,
    }
    defaults.update(overrides)
    return CustomFieldDefinition.objects.create(org=org, **defaults)


@pytest.fixture
def opportunity_a(org_a):
    _set_rls(org_a)
    return Opportunity.objects.create(name="Big Deal", org=org_a)


@pytest.fixture
def opportunity_a2(org_a):
    _set_rls(org_a)
    return Opportunity.objects.create(name="Other Deal", org=org_a)


@pytest.mark.django_db
class TestOpportunityCreateWithCustomFields:
    def test_create_with_valid_dropdown_value(self, admin_client, org_a):
        _make_tier_def(org_a)
        response = admin_client.post(
            OPPORTUNITIES_LIST_URL,
            {"name": "Tiered Deal", "custom_fields": {"deal_tier": "strategic"}},
            format="json",
        )
        assert response.status_code == 200, response.content
        opp = Opportunity.objects.get(name="Tiered Deal", org=org_a)
        assert opp.custom_fields == {"deal_tier": "strategic"}

    def test_create_rejects_invalid_dropdown_value(self, admin_client, org_a):
        _make_tier_def(org_a)
        response = admin_client.post(
            OPPORTUNITIES_LIST_URL,
            {"name": "Bad Tier Deal", "custom_fields": {"deal_tier": "platinum"}},
            format="json",
        )
        assert response.status_code == 400
        assert "custom_fields" in response.json()["errors"]
        assert "deal_tier" in response.json()["errors"]["custom_fields"]

    def test_create_drops_unknown_keys(self, admin_client, org_a):
        _make_tier_def(org_a)
        response = admin_client.post(
            OPPORTUNITIES_LIST_URL,
            {
                "name": "Unknown Key Deal",
                "custom_fields": {"deal_tier": "strategic", "made_up": "ignored"},
            },
            format="json",
        )
        assert response.status_code == 200
        opp = Opportunity.objects.get(name="Unknown Key Deal", org=org_a)
        assert opp.custom_fields == {"deal_tier": "strategic"}

    def test_create_required_missing_returns_400(self, admin_client, org_a):
        _make_tier_def(org_a, is_required=True)
        response = admin_client.post(
            OPPORTUNITIES_LIST_URL,
            {"name": "No CF Deal"},
            format="json",
        )
        assert response.status_code == 400
        assert "deal_tier" in response.json()["errors"]["custom_fields"]


@pytest.mark.django_db
class TestOpportunityUpdateWithCustomFields:
    def test_patch_merges_with_existing(self, admin_client, opportunity_a, org_a):
        _make_tier_def(org_a)
        _make_tier_def(
            org_a,
            key="forecast_score",
            field_type="number",
            options=None,
        )
        opportunity_a.custom_fields = {"deal_tier": "strategic"}
        opportunity_a.save()

        response = admin_client.patch(
            f"{OPPORTUNITIES_LIST_URL}{opportunity_a.id}/",
            {"custom_fields": {"forecast_score": 87}},
            format="json",
        )
        assert response.status_code == 200, response.content
        opportunity_a.refresh_from_db()
        assert opportunity_a.custom_fields == {
            "deal_tier": "strategic",
            "forecast_score": 87.0,
        }

    def test_patch_invalid_returns_400(self, admin_client, opportunity_a, org_a):
        _make_tier_def(org_a)
        response = admin_client.patch(
            f"{OPPORTUNITIES_LIST_URL}{opportunity_a.id}/",
            {"custom_fields": {"deal_tier": "platinum"}},
            format="json",
        )
        assert response.status_code == 400

    def test_put_replaces_custom_fields(self, admin_client, opportunity_a, org_a):
        _make_tier_def(org_a)
        opportunity_a.custom_fields = {"deal_tier": "standard"}
        opportunity_a.save()

        response = admin_client.put(
            f"{OPPORTUNITIES_LIST_URL}{opportunity_a.id}/",
            {"name": opportunity_a.name, "custom_fields": {"deal_tier": "strategic"}},
            format="json",
        )
        assert response.status_code == 200, response.content
        opportunity_a.refresh_from_db()
        assert opportunity_a.custom_fields == {"deal_tier": "strategic"}


@pg_only
@pytest.mark.django_db
class TestOpportunityListFilter:
    def test_cf_filter_returns_matching(
        self, admin_client, opportunity_a, opportunity_a2, org_a
    ):
        _make_tier_def(org_a)
        opportunity_a.custom_fields = {"deal_tier": "strategic"}
        opportunity_a.save()
        opportunity_a2.custom_fields = {"deal_tier": "standard"}
        opportunity_a2.save()

        response = admin_client.get(f"{OPPORTUNITIES_LIST_URL}?cf_deal_tier=strategic")
        body = response.json()
        ids = [o["id"] for o in body["opportunities"]]
        assert str(opportunity_a.id) in ids
        assert str(opportunity_a2.id) not in ids


@pytest.mark.django_db
class TestOpportunityDetailResponse:
    def test_detail_includes_definitions_and_values(
        self, admin_client, opportunity_a, org_a
    ):
        _make_tier_def(org_a)
        opportunity_a.custom_fields = {"deal_tier": "standard"}
        opportunity_a.save()

        response = admin_client.get(f"{OPPORTUNITIES_LIST_URL}{opportunity_a.id}/")
        assert response.status_code == 200, response.content
        body = response.json()
        assert body["opportunity_obj"]["custom_fields"] == {"deal_tier": "standard"}
        keys = [d["key"] for d in body["custom_field_definitions"]]
        assert "deal_tier" in keys

    def test_detail_excludes_inactive_definitions(
        self, admin_client, opportunity_a, org_a
    ):
        _make_tier_def(org_a)
        _make_tier_def(
            org_a, key="legacy", field_type="text", options=None, is_active=False
        )
        response = admin_client.get(f"{OPPORTUNITIES_LIST_URL}{opportunity_a.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "deal_tier" in keys
        assert "legacy" not in keys

    def test_cross_org_does_not_leak_definitions(
        self, admin_client, opportunity_a, org_a, org_b
    ):
        CustomFieldDefinition.objects.create(
            org=org_b,
            target_model="Opportunity",
            key="other_org_field",
            label="Other org",
            field_type="text",
        )
        response = admin_client.get(f"{OPPORTUNITIES_LIST_URL}{opportunity_a.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "other_org_field" not in keys
