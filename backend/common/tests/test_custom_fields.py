"""Tests for the generic custom-fields foundation: CustomFieldDefinition model,
the validate_payload helper, and the /api/custom-fields/ admin API.

See docs/cases/tier1/custom-fields.md.
"""

from __future__ import annotations

import pytest

from cases.models import Case
from common.custom_fields import validate_definition_options, validate_payload
from common.models import CustomFieldDefinition
from common.tests.object_records import make_record
from conftest import rls_org
from leads.models import Lead


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
            validate_definition_options("text", [{"value": "x", "label": "y"}])

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
        self._defn(org_a, key="hours", field_type="number", options=None)
        cleaned, errors = validate_payload("Case", {"hours": "abc"}, org_a)
        assert "hours" in errors

    def test_checkbox_string_coercion(self, org_a):
        self._defn(org_a, key="vip", field_type="checkbox", options=None)
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

    def test_inactive_definition_preserves_existing_value(self, org_a):
        """Soft-deleting a definition must NOT wipe historical values on
        the next save. Admins can deactivate a field without data loss."""
        self._defn(org_a, is_active=False)
        cleaned, errors = validate_payload(
            "Case", {}, org_a, existing={"severity": "S1"}
        )
        assert errors == {}
        assert cleaned == {"severity": "S1"}

    def test_inactive_field_sent_back_keeps_its_stored_value(self, org_a):
        """The phone sends a record's whole stored map back on save, so a
        turned-off field arrives with its own value. Sending the key must not
        erase what leaving it out would have kept."""
        self._defn(org_a, is_active=False)
        cleaned, errors = validate_payload(
            "Case", {"severity": "S1"}, org_a, existing={"severity": "S1"}
        )
        assert errors == {}
        assert cleaned == {"severity": "S1"}

    @pytest.mark.parametrize("sent", ["S2", None, ""])
    def test_inactive_field_cannot_be_changed_or_cleared(self, org_a, sent):
        self._defn(org_a, is_active=False)
        cleaned, errors = validate_payload(
            "Case", {"severity": sent}, org_a, existing={"severity": "S1"}
        )
        assert errors == {}
        assert cleaned == {"severity": "S1"}

    def test_removed_option_sent_back_unchanged_is_kept(self, org_a):
        """A record still holding an option an admin has since removed must
        stay savable. Its value comes back exactly as stored and is kept."""
        self._defn(org_a)
        cleaned, errors = validate_payload(
            "Case", {"severity": "S9"}, org_a, existing={"severity": "S9"}
        )
        assert errors == {}
        assert cleaned == {"severity": "S9"}

    def test_removed_option_cannot_replace_another_value(self, org_a):
        self._defn(org_a)
        cleaned, errors = validate_payload(
            "Case", {"severity": "S9"}, org_a, existing={"severity": "S1"}
        )
        assert "severity" in errors

    def test_unchanged_value_keeps_the_stored_copy(self, org_a):
        """A value equal to the stored one skips validation, and the stored
        copy is what gets kept, so nothing a request sends is written
        unchecked: `1 == True` keeps the stored boolean, not the integer."""
        self._defn(org_a, key="vip", field_type="checkbox", options=None)
        cleaned, errors = validate_payload(
            "Case", {"vip": 1}, org_a, existing={"vip": True}
        )
        assert errors == {}
        assert cleaned["vip"] is True

    def test_whole_number_against_stored_float_is_unchanged(self, org_a):
        self._defn(org_a, key="hours", field_type="number", options=None)
        cleaned, errors = validate_payload(
            "Case", {"hours": 3}, org_a, existing={"hours": 3.0}
        )
        assert errors == {}
        assert cleaned == {"hours": 3.0}

    # The phone's lead form clears a text field with an empty string; the
    # web and the phone's shared custom-fields form send null.
    @pytest.mark.parametrize("sent", ["", None])
    def test_empty_value_clears_field(self, org_a, sent):
        self._defn(org_a)
        cleaned, errors = validate_payload(
            "Case", {"severity": sent}, org_a, existing={"severity": "S1"}
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
        assert (
            CustomFieldDefinition.objects.filter(org=org_a, key="severity").count() == 1
        )

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
            org=org_a,
            target_model="Case",
            key="b",
            label="B",
            field_type="text",
            is_active=False,
        )
        response = admin_client.get(self.URL + "?target_model=Case&active_only=true")
        keys = [d["key"] for d in response.json()["definitions"]]
        assert keys == ["a"]

    def test_get_include_counts_false_omits_the_expensive_counts(
        self, admin_client, org_a
    ):
        """`records_missing_value` is one COUNT over every record of the target
        model per definition. Record pages fetch definitions only for labels and
        types, so they opt out; the payload must then carry neither the per-row
        count nor the totals block."""
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Lead",
            key="budget",
            label="Budget",
            field_type="number",
        )
        response = admin_client.get(
            self.URL + "?target_model=Lead&include_counts=false"
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["definitions"]) == 1
        assert body["definitions"][0]["key"] == "budget"
        assert "records_missing_value" not in body["definitions"][0]
        assert body["totals"] is None

    def test_get_counts_included_by_default(self, admin_client, org_a):
        """The opt-out must be opt-in: an unqualified GET, and an explicit
        anything-other-than-"false", keep the settings page's numbers."""
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Lead",
            key="budget",
            label="Budget",
            field_type="number",
        )
        for query in ("?target_model=Lead", "?target_model=Lead&include_counts=true"):
            body = admin_client.get(self.URL + query).json()
            assert "records_missing_value" in body["definitions"][0], query
            assert body["totals"] is not None, query
            assert body["totals"]["count"] == 1, query

    def test_get_allowed_for_non_admin(self, user_client, org_a):
        # Non-admins read definitions so the case detail page can render fields.
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Case",
            key="severity",
            label="Severity",
            field_type="text",
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
            {
                "label": "Severity Level",
                "options": [
                    {"value": "S1", "label": "S1"},
                    {"value": "S2", "label": "S2"},
                ],
            },
            format="json",
        )
        assert response.status_code == 200, response.content
        defn.refresh_from_db()
        assert defn.label == "Severity Level"
        assert len(defn.options) == 2

    def test_put_rejects_key_change(self, admin_client, org_a):
        defn = CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Case",
            key="severity",
            label="Severity",
            field_type="text",
        )
        response = admin_client.put(
            f"{self.URL}{defn.id}/", {"key": "severity_new"}, format="json"
        )
        assert response.status_code == 400
        assert "key" in str(response.content)

    def test_put_rejects_field_type_change(self, admin_client, org_a):
        defn = CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Case",
            key="severity",
            label="Severity",
            field_type="text",
        )
        response = admin_client.put(
            f"{self.URL}{defn.id}/", {"field_type": "number"}, format="json"
        )
        assert response.status_code == 400

    def test_delete_soft_deactivates(self, admin_client, org_a):
        defn = CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Case",
            key="severity",
            label="Severity",
            field_type="text",
        )
        response = admin_client.delete(f"{self.URL}{defn.id}/")
        assert response.status_code == 200
        defn.refresh_from_db()
        assert defn.is_active is False

    def test_delete_non_admin_forbidden(self, user_client, org_a):
        defn = CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Case",
            key="severity",
            label="Severity",
            field_type="text",
        )
        response = user_client.delete(f"{self.URL}{defn.id}/")
        assert response.status_code == 403

    def test_unsupported_target_rejected(self, admin_client):
        response = admin_client.post(
            self.URL,
            self._payload(target_model="Comment"),
            format="json",
        )
        assert response.status_code == 400
        assert "target_model" in response.json()["errors"]

    def test_duplicate_key_per_target_rejected(self, admin_client, org_a):
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Case",
            key="severity",
            label="Severity",
            field_type="text",
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


@pytest.mark.django_db
class TestCustomFieldAnalytics:
    """records_missing_value + totals, the settings/custom-fields stat cards."""

    URL = "/api/custom-fields/"

    def _case(self, org, custom_fields):
        return Case.objects.create(
            org=org,
            name="C",
            status="New",
            priority="Normal",
            custom_fields=custom_fields,
        )

    def _row(self, response, key):
        return next(d for d in response.json()["definitions"] if d["key"] == key)

    def test_records_missing_value_counts_rows_without_the_key(
        self, admin_client, org_a
    ):
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Case",
            key="severity",
            label="Severity",
            field_type="text",
            is_required=True,
        )
        self._case(org_a, {"severity": "S1"})  # has a value
        self._case(org_a, {})  # missing
        self._case(org_a, {"other": "x"})  # missing (different key)

        row = self._row(admin_client.get(self.URL), "severity")
        assert row["records_missing_value"] == 2

    def test_totals_count_active_models_and_gaps(self, admin_client, org_a):
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Case",
            key="severity",
            label="S",
            field_type="text",
            is_required=True,
        )
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Case",
            key="region",
            label="R",
            field_type="text",
            is_required=False,
        )
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Lead",
            key="score",
            label="Sc",
            field_type="text",
            is_required=True,
        )
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Case",
            key="legacy",
            label="L",
            field_type="text",
            is_active=False,
        )
        self._case(org_a, {})  # missing severity + region
        self._case(org_a, {"severity": "S1", "region": "eu"})  # has both
        Lead.objects.create(org=org_a, custom_fields={})  # missing score

        totals = admin_client.get(self.URL).json()["totals"]
        assert totals == {
            "count": 4,  # includes the inactive legacy field
            "active": 3,
            "models_extended": 2,  # Case + Lead have active fields
            # severity (1 case missing) + score (1 lead missing); region isn't
            # required, legacy is inactive & not required.
            "required_with_gaps": 2,
        }

    def test_records_missing_value_is_org_scoped(self, admin_client, org_a, org_b):
        """The record count must not include another org's rows. Proven on
        SQLite where RLS is inert, so only the explicit org filter scopes it."""
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Case",
            key="severity",
            label="S",
            field_type="text",
            is_required=True,
        )
        self._case(org_a, {})  # one org_a case, missing the value
        for _ in range(3):
            self._case(org_b, {})  # foreign-org cases must not be counted

        row = self._row(admin_client.get(self.URL), "severity")
        assert row["records_missing_value"] == 1  # not 4

    def test_non_admin_sees_analytics(self, user_client, org_a):
        # Reads are open to members (shared config), analytics included.
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Case",
            key="severity",
            label="S",
            field_type="text",
        )
        resp = user_client.get(self.URL)
        assert resp.status_code == 200
        assert "totals" in resp.json()
        assert resp.json()["definitions"][0]["records_missing_value"] == 0


TARGET_KEYS = {
    "Account": "account",
    "Case": "ticket",
    "Contact": "contact",
    "Estimate": "estimate",
    "Invoice": "invoice",
    "Lead": "lead",
    "Opportunity": "deal",
    "RecurringInvoice": "recurring_invoice",
    "Task": "task",
}


@pytest.mark.django_db
class TestEveryTarget:
    URL = "/api/custom-fields/"

    @pytest.mark.parametrize("target", TARGET_KEYS)
    def test_an_admin_creates_a_definition_on_every_target(self, target, admin_client):
        payload = TestCustomFieldDefinitionAPI()._payload(target_model=target)
        response = admin_client.post(self.URL, payload, format="json")
        assert response.status_code == 201, response.content

    @pytest.mark.parametrize("value", ["Comment", "", "x" * 33])
    def test_a_bad_target_gets_todays_exact_error(self, value, admin_client):
        payload = TestCustomFieldDefinitionAPI()._payload(target_model=value)
        response = admin_client.post(self.URL, payload, format="json")
        assert response.status_code == 400
        assert response.json()["errors"]["target_model"] == [
            f'"{value}" is not a valid choice.'
        ]

    def test_missing_counts_and_totals_cover_every_target(
        self, admin_client, org_a, org_b
    ):
        for target, key in TARGET_KEYS.items():
            CustomFieldDefinition.objects.create(
                org=org_a,
                target_model=target,
                key="probe",
                label="Probe",
                field_type="text",
                is_required=True,
            )
            make_record(key, org_a)
            filled = make_record(key, org_a)
            type(filled).objects.filter(pk=filled.pk).update(
                custom_fields={"probe": "set"}
            )
            with rls_org(org_b):
                make_record(key, org_b)
        body = admin_client.get(self.URL).json()
        assert {
            d["target_model"]: d["records_missing_value"] for d in body["definitions"]
        } == dict.fromkeys(TARGET_KEYS, 1)
        assert body["totals"] == {
            "count": 9,
            "active": 9,
            "models_extended": 9,
            "required_with_gaps": 9,
        }

    def test_a_stored_target_the_registry_does_not_know_counts_zero(
        self, admin_client, org_a
    ):
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Ghost",
            key="probe",
            label="Probe",
            field_type="text",
        )
        response = admin_client.get(self.URL)
        assert response.status_code == 200
        (row,) = response.json()["definitions"]
        assert row["records_missing_value"] == 0
