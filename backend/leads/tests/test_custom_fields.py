"""Leads-side tests for custom fields: Lead create/update payloads, list filter,
detail-page response shape, and the converted+custom_fields regression.

Mirrors cases/tests/test_custom_fields.py. See docs/cases/tier1/custom-fields.md
for the underlying contract.
"""

from __future__ import annotations

import pytest
from django.db import connection

from common.models import CustomFieldDefinition
from leads.models import Lead

pg_only = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="JSONField __contains lookup requires PostgreSQL",
)


LEADS_LIST_URL = "/api/leads/"


def _set_rls(org):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.current_org', %s, false)", [str(org.id)]
        )


def _make_severity_def(org, **overrides):
    defaults = {
        "target_model": "Lead",
        "key": "severity",
        "label": "Severity",
        "field_type": "dropdown",
        "options": [{"value": "S1", "label": "S1"}, {"value": "S2", "label": "S2"}],
        "is_required": False,
        "is_active": True,
    }
    defaults.update(overrides)
    return CustomFieldDefinition.objects.create(org=org, **defaults)


@pytest.fixture
def lead_a(admin_user, org_a):
    _set_rls(org_a)
    return Lead.objects.create(
        first_name="Jane",
        last_name="Smith",
        email="jane@example.com",
        created_by=admin_user,
        org=org_a,
    )


@pytest.fixture
def lead_a2(admin_user, org_a):
    _set_rls(org_a)
    return Lead.objects.create(
        first_name="Second",
        last_name="Lead",
        email="second@example.com",
        created_by=admin_user,
        org=org_a,
    )


@pytest.mark.django_db
class TestLeadCreateWithCustomFields:
    def test_create_with_valid_dropdown_value(self, admin_client, org_a):
        _make_severity_def(org_a)
        response = admin_client.post(
            LEADS_LIST_URL,
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.cf@example.com",
                "custom_fields": {"severity": "S1"},
            },
            format="json",
        )
        assert response.status_code == 200, response.content
        lead = Lead.objects.get(email="jane.cf@example.com", org=org_a)
        assert lead.custom_fields == {"severity": "S1"}

    def test_create_rejects_invalid_dropdown_value(self, admin_client, org_a):
        _make_severity_def(org_a)
        response = admin_client.post(
            LEADS_LIST_URL,
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.bad@example.com",
                "custom_fields": {"severity": "S99"},
            },
            format="json",
        )
        assert response.status_code == 400
        assert "custom_fields" in response.json()["errors"]
        assert "severity" in response.json()["errors"]["custom_fields"]

    def test_create_drops_unknown_keys(self, admin_client, org_a):
        _make_severity_def(org_a)
        response = admin_client.post(
            LEADS_LIST_URL,
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.unk@example.com",
                "custom_fields": {"severity": "S1", "made_up": "ignored"},
            },
            format="json",
        )
        assert response.status_code == 200
        lead = Lead.objects.get(email="jane.unk@example.com", org=org_a)
        assert lead.custom_fields == {"severity": "S1"}

    def test_create_required_missing_returns_400(self, admin_client, org_a):
        _make_severity_def(org_a, is_required=True)
        response = admin_client.post(
            LEADS_LIST_URL,
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.req@example.com",
            },
            format="json",
        )
        assert response.status_code == 400
        assert "severity" in response.json()["errors"]["custom_fields"]


@pytest.mark.django_db
class TestLeadUpdateWithCustomFields:
    def test_patch_merges_with_existing(self, admin_client, lead_a, org_a):
        _make_severity_def(org_a)
        _make_severity_def(
            org_a,
            key="hours",
            field_type="number",
            options=None,
        )
        lead_a.custom_fields = {"severity": "S1"}
        lead_a.save()

        response = admin_client.patch(
            f"{LEADS_LIST_URL}{lead_a.id}/",
            {"custom_fields": {"hours": 4}},
            format="json",
        )
        assert response.status_code == 200, response.content
        lead_a.refresh_from_db()
        assert lead_a.custom_fields == {"severity": "S1", "hours": 4.0}

    def test_patch_invalid_returns_400(self, admin_client, lead_a, org_a):
        _make_severity_def(org_a)
        response = admin_client.patch(
            f"{LEADS_LIST_URL}{lead_a.id}/",
            {"custom_fields": {"severity": "S99"}},
            format="json",
        )
        assert response.status_code == 400

    def test_patch_converted_persists_custom_fields(
        self, admin_client, lead_a, org_a
    ):
        """Regression for the silent-drop bug: PATCH with both status=converted
        and custom_fields used to discard the fields because the conversion
        branch returned before the validate/save block."""
        _make_severity_def(org_a)
        response = admin_client.patch(
            f"{LEADS_LIST_URL}{lead_a.id}/",
            {"status": "converted", "custom_fields": {"severity": "S2"}},
            format="json",
        )
        assert response.status_code == 200, response.content
        lead_a.refresh_from_db()
        assert lead_a.custom_fields == {"severity": "S2"}

    def test_patch_converted_rejects_invalid_custom_fields(
        self, admin_client, lead_a, org_a
    ):
        """Validation must run before conversion — bad payload should 400, not
        get smuggled through."""
        _make_severity_def(org_a)
        response = admin_client.patch(
            f"{LEADS_LIST_URL}{lead_a.id}/",
            {"status": "converted", "custom_fields": {"severity": "S99"}},
            format="json",
        )
        assert response.status_code == 400
        lead_a.refresh_from_db()
        # Lead must not have been converted, and no custom_fields written.
        assert lead_a.status != "converted"
        assert lead_a.custom_fields in (None, {}, {"severity": None})


@pg_only
@pytest.mark.django_db
class TestLeadListFilter:
    def test_cf_filter_returns_matching(
        self, admin_client, lead_a, lead_a2, org_a
    ):
        _make_severity_def(org_a)
        lead_a.custom_fields = {"severity": "S1"}
        lead_a.save()
        lead_a2.custom_fields = {"severity": "S2"}
        lead_a2.save()

        response = admin_client.get(f"{LEADS_LIST_URL}?cf_severity=S1")
        body = response.json()
        ids = [lead["id"] for lead in body["open_leads"]["open_leads"]]
        assert str(lead_a.id) in ids
        assert str(lead_a2.id) not in ids


@pytest.mark.django_db
class TestLeadDetailResponse:
    def test_detail_includes_definitions_and_values(
        self, admin_client, lead_a, org_a
    ):
        _make_severity_def(org_a)
        lead_a.custom_fields = {"severity": "S2"}
        lead_a.save()

        response = admin_client.get(f"{LEADS_LIST_URL}{lead_a.id}/")
        assert response.status_code == 200, response.content
        body = response.json()
        assert body["lead_obj"]["custom_fields"] == {"severity": "S2"}
        keys = [d["key"] for d in body["custom_field_definitions"]]
        assert "severity" in keys

    def test_detail_excludes_inactive_definitions(
        self, admin_client, lead_a, org_a
    ):
        _make_severity_def(org_a)
        _make_severity_def(
            org_a, key="legacy", field_type="text", options=None, is_active=False
        )
        response = admin_client.get(f"{LEADS_LIST_URL}{lead_a.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "severity" in keys
        assert "legacy" not in keys

    def test_cross_org_does_not_leak_definitions(
        self, admin_client, lead_a, org_a, org_b
    ):
        CustomFieldDefinition.objects.create(
            org=org_b,
            target_model="Lead",
            key="other_org_field",
            label="Other org",
            field_type="text",
        )
        response = admin_client.get(f"{LEADS_LIST_URL}{lead_a.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "other_org_field" not in keys
