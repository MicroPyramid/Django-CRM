"""Tests for the generic custom-fields foundation: CustomFieldDefinition model,
the validate_payload helper, and the /api/custom-fields/ admin API.

See docs/cases/tier1/custom-fields.md.
"""

from __future__ import annotations

import pytest

from common.custom_fields import validate_definition_options, validate_payload
from common.models import CustomFieldDefinition


@pytest.mark.django_db
class TestValidatorHelpers:
    def test_dropdown_options_must_be_nonempty_list(self):
        with pytest.raises(Exception):
            validate_definition_options("dropdown", None)
        with pytest.raises(Exception):
            validate_definition_options("dropdown", [])

    def test_dropdown_options_reject_duplicates(self):
        with pytest.raises(Exception):
            validate_definition_options(
                "dropdown",
                [{"value": "S1", "label": "S1"}, {"value": "S1", "label": "Duplicate"}],
            )

    def test_options_forbidden_for_non_dropdown(self):
        with pytest.raises(Exception):
            validate_definition_options(
                "text", [{"value": "x", "label": "y"}]
            )

    def test_options_none_ok_for_non_dropdown(self):
        validate_definition_options("text", None)
        validate_definition_options("number", None)


@pytest.mark.django_db
class TestValidatePayload:
    def _defn(self, org, **kwargs):
        defaults = {
            "target_model": "Case",
            "key": "severity",
            "label": "Severity",
            "field_type": "dropdown",
            "options": [
                {"value": "S1", "label": "S1"},
                {"value": "S2", "label": "S2"},
            ],
            "is_required": False,
            "is_active": True,
        }
        defaults.update(kwargs)
        return CustomFieldDefinition.objects.create(org=org, **defaults)

    def test_unknown_keys_dropped(self, org_a):
        self._defn(org_a)
        cleaned, errors = validate_payload(
            "Case", {"severity": "S1", "made_up": "nope"}, org_a
        )
        assert errors == {}
        assert cleaned == {"severity": "S1"}

    def test_dropdown_invalid_value_rejected(self, org_a):
        self._defn(org_a)
        cleaned, errors = validate_payload("Case", {"severity": "S99"}, org_a)
        assert "severity" in errors
        assert cleaned == {}

    def test_required_field_missing_errors(self, org_a):
        self._defn(org_a, is_required=True)
        cleaned, errors = validate_payload("Case", {}, org_a)
        assert errors.get("severity") == "is required"

    def test_required_field_preserved_from_existing(self, org_a):
        self._defn(org_a, is_required=True)
        cleaned, errors = validate_payload(
            "Case", {}, org_a, existing={"severity": "S1"}
        )
        assert errors == {}
        assert cleaned == {"severity": "S1"}

    def test_number_coercion(self, org_a):
        self._defn(
            org_a, key="hours", field_type="number", options=None, is_required=False
        )
        cleaned, errors = validate_payload("Case", {"hours": "3.5"}, org_a)
        assert errors == {}
        assert cleaned == {"hours": 3.5}

    def test_number_invalid_errors(self, org_a):
        self._defn(
            org_a, key="hours", field_type="number", options=None
        )
        cleaned, errors = validate_payload("Case", {"hours": "abc"}, org_a)
        assert "hours" in errors

    def test_checkbox_string_coercion(self, org_a):
        self._defn(
            org_a, key="vip", field_type="checkbox", options=None
        )
        cleaned, errors = validate_payload("Case", {"vip": "true"}, org_a)
        assert errors == {}
        assert cleaned == {"vip": True}

    def test_date_iso_validated(self, org_a):
        self._defn(org_a, key="due", field_type="date", options=None)
        cleaned, errors = validate_payload("Case", {"due": "2026-08-01"}, org_a)
        assert errors == {}
        assert cleaned == {"due": "2026-08-01"}

        cleaned, errors = validate_payload("Case", {"due": "not-a-date"}, org_a)
        assert "due" in errors

    def test_inactive_definition_treated_as_unknown(self, org_a):
        self._defn(org_a, is_active=False)
        cleaned, errors = validate_payload("Case", {"severity": "S1"}, org_a)
        # Inactive definition: drop silently, no error.
        assert cleaned == {}
        assert errors == {}

    def test_empty_value_clears_field(self, org_a):
        self._defn(org_a)
        cleaned, errors = validate_payload(
            "Case", {"severity": ""}, org_a, existing={"severity": "S1"}
        )
        assert cleaned == {}
        assert errors == {}


@pytest.mark.django_db
class TestCustomFieldDefinitionAPI:
    URL = "/api/custom-fields/"

    def _payload(self, **overrides):
        body = {
            "target_model": "Case",
            "key": "severity",
            "label": "Severity",
            "field_type": "dropdown",
            "options": [
                {"value": "S1", "label": "S1"},
                {"value": "S2", "label": "S2"},
            ],
            "is_required": False,
            "is_filterable": True,
            "display_order": 0,
            "is_active": True,
        }
        body.update(overrides)
        return body

    def test_post_admin_creates(self, admin_client, org_a):
        response = admin_client.post(self.URL, self._payload(), format="json")
        assert response.status_code == 201, response.content
        body = response.json()
        assert body["key"] == "severity"
        assert CustomFieldDefinition.objects.filter(org=org_a, key="severity").count() == 1

    def test_post_non_admin_forbidden(self, user_client):
        response = user_client.post(self.URL, self._payload(), format="json")
        assert response.status_code == 403

    def test_get_lists_definitions(self, admin_client, org_a):
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Case",
            key="severity",
            label="Severity",
            field_type="text",
        )
        response = admin_client.get(self.URL + "?target_model=Case")
        assert response.status_code == 200
        body = response.json()
        assert len(body["definitions"]) == 1
        assert body["definitions"][0]["key"] == "severity"

    def test_get_filters_active_only(self, admin_client, org_a):
        CustomFieldDefinition.objects.create(
            org=org_a, target_model="Case", key="a", label="A", field_type="text"
        )
        CustomFieldDefinition.objects.create(
            org=org_a, target_model="Case", key="b", label="B", field_type="text",
            is_active=False,
        )
        response = admin_client.get(self.URL + "?target_model=Case&active_only=true")
        keys = [d["key"] for d in response.json()["definitions"]]
        assert keys == ["a"]

    def test_get_allowed_for_non_admin(self, user_client, org_a):
        # Non-admins read definitions so the case detail page can render fields.
        CustomFieldDefinition.objects.create(
            org=org_a, target_model="Case", key="severity", label="Severity", field_type="text",
        )
        response = user_client.get(self.URL + "?target_model=Case")
        assert response.status_code == 200

    def test_put_updates_label_and_options(self, admin_client, org_a):
        defn = CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Case",
            key="severity",
            label="Severity",
            field_type="dropdown",
            options=[{"value": "S1", "label": "S1"}],
        )
        response = admin_client.put(
            f"{self.URL}{defn.id}/",
            {"label": "Severity Level", "options": [{"value": "S1", "label": "S1"}, {"value": "S2", "label": "S2"}]},
            format="json",
        )
        assert response.status_code == 200, response.content
        defn.refresh_from_db()
        assert defn.label == "Severity Level"
        assert len(defn.options) == 2

    def test_put_rejects_key_change(self, admin_client, org_a):
        defn = CustomFieldDefinition.objects.create(
            org=org_a, target_model="Case", key="severity", label="Severity", field_type="text",
        )
        response = admin_client.put(
            f"{self.URL}{defn.id}/", {"key": "severity_new"}, format="json"
        )
        assert response.status_code == 400
        assert "key" in str(response.content)

    def test_put_rejects_field_type_change(self, admin_client, org_a):
        defn = CustomFieldDefinition.objects.create(
            org=org_a, target_model="Case", key="severity", label="Severity", field_type="text",
        )
        response = admin_client.put(
            f"{self.URL}{defn.id}/", {"field_type": "number"}, format="json"
        )
        assert response.status_code == 400

    def test_delete_soft_deactivates(self, admin_client, org_a):
        defn = CustomFieldDefinition.objects.create(
            org=org_a, target_model="Case", key="severity", label="Severity", field_type="text",
        )
        response = admin_client.delete(f"{self.URL}{defn.id}/")
        assert response.status_code == 200
        defn.refresh_from_db()
        assert defn.is_active is False

    def test_delete_non_admin_forbidden(self, user_client, org_a):
        defn = CustomFieldDefinition.objects.create(
            org=org_a, target_model="Case", key="severity", label="Severity", field_type="text",
        )
        response = user_client.delete(f"{self.URL}{defn.id}/")
        assert response.status_code == 403

    def test_unsupported_target_rejected(self, admin_client):
        response = admin_client.post(
            self.URL,
            self._payload(target_model="Lead"),
            format="json",
        )
        assert response.status_code == 400
        assert "target_model" in response.json()["errors"]

    def test_duplicate_key_per_target_rejected(self, admin_client, org_a):
        CustomFieldDefinition.objects.create(
            org=org_a, target_model="Case", key="severity", label="Severity", field_type="text",
        )
        response = admin_client.post(self.URL, self._payload(), format="json")
        assert response.status_code == 400

    def test_invalid_key_format_rejected(self, admin_client):
        response = admin_client.post(
            self.URL, self._payload(key="Severity"), format="json"
        )
        assert response.status_code == 400

    def test_dropdown_without_options_rejected(self, admin_client):
        response = admin_client.post(
            self.URL,
            self._payload(field_type="dropdown", options=None),
            format="json",
        )
        assert response.status_code == 400

    def test_cross_org_isolation(self, admin_client, org_b_client, org_a, org_b):
        admin_client.post(self.URL, self._payload(), format="json")
        org_b_response = org_b_client.get(self.URL + "?target_model=Case")
        assert org_b_response.status_code == 200
        assert org_b_response.json()["definitions"] == []
