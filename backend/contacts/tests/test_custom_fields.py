"""Contacts-side tests for custom fields: Contact create/update payloads, list
filter, detail-page response shape, and cross-org isolation.

Mirrors leads/tests/test_custom_fields.py and cases/tests/test_custom_fields.py.
See docs/cases/tier1/custom-fields.md for the underlying contract.
"""

from __future__ import annotations

import pytest
from django.db import connection

from common.models import CustomFieldDefinition
from contacts.models import Contact

pg_only = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="JSONField __contains lookup requires PostgreSQL",
)


CONTACTS_LIST_URL = "/api/contacts/"


def _set_rls(org):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.current_org', %s, false)", [str(org.id)]
        )


def _make_severity_def(org, **overrides):
    defaults = {
        "target_model": "Contact",
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
def contact_a(admin_user, org_a):
    _set_rls(org_a)
    return Contact.objects.create(
        first_name="Jane",
        last_name="Smith",
        email="jane@example.com",
        created_by=admin_user,
        org=org_a,
    )


@pytest.fixture
def contact_a2(admin_user, org_a):
    _set_rls(org_a)
    return Contact.objects.create(
        first_name="Second",
        last_name="Contact",
        email="second@example.com",
        created_by=admin_user,
        org=org_a,
    )


@pytest.mark.django_db
class TestContactCreateWithCustomFields:
    def test_create_with_valid_dropdown_value(self, admin_client, org_a):
        _make_severity_def(org_a)
        response = admin_client.post(
            CONTACTS_LIST_URL,
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.cf@example.com",
                "custom_fields": {"severity": "S1"},
            },
            format="json",
        )
        assert response.status_code == 200, response.content
        contact = Contact.objects.get(email="jane.cf@example.com", org=org_a)
        assert contact.custom_fields == {"severity": "S1"}

    def test_create_rejects_invalid_dropdown_value(self, admin_client, org_a):
        _make_severity_def(org_a)
        response = admin_client.post(
            CONTACTS_LIST_URL,
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
            CONTACTS_LIST_URL,
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.unk@example.com",
                "custom_fields": {"severity": "S1", "made_up": "ignored"},
            },
            format="json",
        )
        assert response.status_code == 200
        contact = Contact.objects.get(email="jane.unk@example.com", org=org_a)
        assert contact.custom_fields == {"severity": "S1"}

    def test_create_required_missing_returns_400(self, admin_client, org_a):
        _make_severity_def(org_a, is_required=True)
        response = admin_client.post(
            CONTACTS_LIST_URL,
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
class TestContactUpdateWithCustomFields:
    def test_patch_merges_with_existing(self, admin_client, contact_a, org_a):
        _make_severity_def(org_a)
        _make_severity_def(
            org_a,
            key="hours",
            field_type="number",
            options=None,
        )
        contact_a.custom_fields = {"severity": "S1"}
        contact_a.save()

        response = admin_client.patch(
            f"{CONTACTS_LIST_URL}{contact_a.id}/",
            {"custom_fields": {"hours": 4}},
            format="json",
        )
        assert response.status_code == 200, response.content
        contact_a.refresh_from_db()
        assert contact_a.custom_fields == {"severity": "S1", "hours": 4.0}

    def test_patch_invalid_returns_400(self, admin_client, contact_a, org_a):
        _make_severity_def(org_a)
        response = admin_client.patch(
            f"{CONTACTS_LIST_URL}{contact_a.id}/",
            {"custom_fields": {"severity": "S99"}},
            format="json",
        )
        assert response.status_code == 400

    def test_put_replaces_custom_fields(self, admin_client, contact_a, org_a):
        _make_severity_def(org_a)
        contact_a.custom_fields = {"severity": "S1"}
        contact_a.save()

        response = admin_client.put(
            f"{CONTACTS_LIST_URL}{contact_a.id}/",
            {
                "first_name": contact_a.first_name,
                "last_name": contact_a.last_name,
                "email": contact_a.email,
                "custom_fields": {"severity": "S2"},
            },
            format="json",
        )
        assert response.status_code == 200, response.content
        contact_a.refresh_from_db()
        assert contact_a.custom_fields == {"severity": "S2"}


@pg_only
@pytest.mark.django_db
class TestContactListFilter:
    def test_cf_filter_returns_matching(
        self, admin_client, contact_a, contact_a2, org_a
    ):
        _make_severity_def(org_a)
        contact_a.custom_fields = {"severity": "S1"}
        contact_a.save()
        contact_a2.custom_fields = {"severity": "S2"}
        contact_a2.save()

        response = admin_client.get(f"{CONTACTS_LIST_URL}?cf_severity=S1")
        body = response.json()
        ids = [c["id"] for c in body["results"]]
        assert str(contact_a.id) in ids
        assert str(contact_a2.id) not in ids


@pytest.mark.django_db
class TestContactDetailResponse:
    def test_detail_includes_definitions_and_values(
        self, admin_client, contact_a, org_a
    ):
        _make_severity_def(org_a)
        contact_a.custom_fields = {"severity": "S2"}
        contact_a.save()

        response = admin_client.get(f"{CONTACTS_LIST_URL}{contact_a.id}/")
        assert response.status_code == 200, response.content
        body = response.json()
        assert body["contact_obj"]["custom_fields"] == {"severity": "S2"}
        keys = [d["key"] for d in body["custom_field_definitions"]]
        assert "severity" in keys

    def test_detail_excludes_inactive_definitions(
        self, admin_client, contact_a, org_a
    ):
        _make_severity_def(org_a)
        _make_severity_def(
            org_a, key="legacy", field_type="text", options=None, is_active=False
        )
        response = admin_client.get(f"{CONTACTS_LIST_URL}{contact_a.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "severity" in keys
        assert "legacy" not in keys

    def test_cross_org_does_not_leak_definitions(
        self, admin_client, contact_a, org_a, org_b
    ):
        CustomFieldDefinition.objects.create(
            org=org_b,
            target_model="Contact",
            key="other_org_field",
            label="Other org",
            field_type="text",
        )
        response = admin_client.get(f"{CONTACTS_LIST_URL}{contact_a.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "other_org_field" not in keys

    def test_cross_org_does_not_leak_values(self, admin_client, admin_user, org_b):
        """Same CF key in both orgs — admin (org_a) must not GET a contact
        from org_b, so its custom_fields values stay confined to org_b."""
        _set_rls(org_b)
        contact_in_b = Contact.objects.create(
            first_name="Bob",
            last_name="OtherOrg",
            email="bob@other.example.com",
            created_by=admin_user,
            org=org_b,
            custom_fields={"severity": "S2"},
        )
        response = admin_client.get(f"{CONTACTS_LIST_URL}{contact_in_b.id}/")
        assert response.status_code == 404
