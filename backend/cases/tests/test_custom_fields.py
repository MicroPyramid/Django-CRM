"""Cases-side tests for custom fields: Case create/update payloads, list filter,
and detail-page response shape.

See docs/cases/tier1/custom-fields.md.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.db import connection

from cases.models import Case
from common.models import CustomFieldDefinition

pg_only = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="JSONField __contains lookup requires PostgreSQL",
)


CASES_LIST_URL = "/api/cases/"


def _make_severity_def(org, **overrides):
    defaults = {
        "target_model": "Case",
        "key": "severity",
        "label": "Severity",
        "field_type": "dropdown",
        "options": [{"value": "S1", "label": "S1"}, {"value": "S2", "label": "S2"}],
        "is_required": False,
        "is_active": True,
    }
    defaults.update(overrides)
    return CustomFieldDefinition.objects.create(org=org, **defaults)


@pytest.mark.django_db
class TestCaseCreateWithCustomFields:
    @patch("cases.views.send_email_to_assigned_user")
    def test_create_with_valid_dropdown_value(self, mock_email, admin_client, org_a):
        _make_severity_def(org_a)
        response = admin_client.post(
            CASES_LIST_URL,
            {
                "name": "Login crash",
                "status": "New",
                "priority": "High",
                "custom_fields": {"severity": "S1"},
            },
            format="json",
        )
        assert response.status_code == 200, response.content
        case_id = response.data["id"]
        case = Case.objects.get(pk=case_id)
        assert case.custom_fields == {"severity": "S1"}

    @patch("cases.views.send_email_to_assigned_user")
    def test_create_rejects_invalid_dropdown_value(self, mock_email, admin_client, org_a):
        _make_severity_def(org_a)
        response = admin_client.post(
            CASES_LIST_URL,
            {
                "name": "Login crash",
                "status": "New",
                "priority": "High",
                "custom_fields": {"severity": "S99"},
            },
            format="json",
        )
        assert response.status_code == 400
        assert "custom_fields" in response.json()["errors"]
        assert "severity" in response.json()["errors"]["custom_fields"]

    @patch("cases.views.send_email_to_assigned_user")
    def test_create_drops_unknown_keys(self, mock_email, admin_client, org_a):
        _make_severity_def(org_a)
        response = admin_client.post(
            CASES_LIST_URL,
            {
                "name": "Login crash",
                "status": "New",
                "priority": "High",
                "custom_fields": {"severity": "S1", "made_up": "ignored"},
            },
            format="json",
        )
        assert response.status_code == 200
        case = Case.objects.get(pk=response.data["id"])
        assert case.custom_fields == {"severity": "S1"}

    @patch("cases.views.send_email_to_assigned_user")
    def test_create_required_missing_returns_400(self, mock_email, admin_client, org_a):
        _make_severity_def(org_a, is_required=True)
        response = admin_client.post(
            CASES_LIST_URL,
            {
                "name": "Login crash",
                "status": "New",
                "priority": "High",
            },
            format="json",
        )
        assert response.status_code == 400
        assert "severity" in response.json()["errors"]["custom_fields"]


@pytest.mark.django_db
class TestCaseUpdateWithCustomFields:
    @patch("cases.views.send_email_to_assigned_user")
    def test_patch_merges_with_existing(self, mock_email, admin_client, case_a, org_a):
        _make_severity_def(org_a)
        _make_severity_def(
            org_a,
            key="hours",
            field_type="number",
            options=None,
        )
        case_a.custom_fields = {"severity": "S1"}
        case_a.save()

        response = admin_client.patch(
            f"{CASES_LIST_URL}{case_a.id}/",
            {"custom_fields": {"hours": 4}},
            format="json",
        )
        assert response.status_code == 200, response.content
        case_a.refresh_from_db()
        # severity preserved, hours added.
        assert case_a.custom_fields == {"severity": "S1", "hours": 4.0}

    @patch("cases.views.send_email_to_assigned_user")
    def test_patch_invalid_returns_400(self, mock_email, admin_client, case_a, org_a):
        _make_severity_def(org_a)
        response = admin_client.patch(
            f"{CASES_LIST_URL}{case_a.id}/",
            {"custom_fields": {"severity": "S99"}},
            format="json",
        )
        assert response.status_code == 400


@pg_only
@pytest.mark.django_db
class TestCaseListFilter:
    @patch("cases.views.send_email_to_assigned_user")
    def test_cf_filter_returns_matching(
        self, mock_email, admin_client, case_a, case_b_same_org, org_a
    ):
        _make_severity_def(org_a)
        case_a.custom_fields = {"severity": "S1"}
        case_a.save()
        case_b_same_org.custom_fields = {"severity": "S2"}
        case_b_same_org.save()

        response = admin_client.get(f"{CASES_LIST_URL}?cf_severity=S1")
        ids = [c["id"] for c in response.json()["cases"]]
        assert str(case_a.id) in ids
        assert str(case_b_same_org.id) not in ids


@pytest.mark.django_db
class TestCaseDetailResponse:
    def test_detail_includes_definitions_and_values(
        self, admin_client, case_a, org_a
    ):
        defn = _make_severity_def(org_a)
        case_a.custom_fields = {"severity": "S2"}
        case_a.save()

        response = admin_client.get(f"{CASES_LIST_URL}{case_a.id}/")
        assert response.status_code == 200, response.content
        body = response.json()
        assert body["cases_obj"]["custom_fields"] == {"severity": "S2"}
        keys = [d["key"] for d in body["custom_field_definitions"]]
        assert "severity" in keys

    def test_detail_excludes_inactive_definitions(
        self, admin_client, case_a, org_a
    ):
        _make_severity_def(org_a)
        _make_severity_def(org_a, key="legacy", field_type="text", options=None, is_active=False)
        response = admin_client.get(f"{CASES_LIST_URL}{case_a.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "severity" in keys
        assert "legacy" not in keys

    def test_cross_org_does_not_leak_definitions(
        self, admin_client, case_a, org_a, org_b
    ):
        # A definition in a different org must not appear here.
        CustomFieldDefinition.objects.create(
            org=org_b,
            target_model="Case",
            key="other_org_field",
            label="Other org",
            field_type="text",
        )
        response = admin_client.get(f"{CASES_LIST_URL}{case_a.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "other_org_field" not in keys
