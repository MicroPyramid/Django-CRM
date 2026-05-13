"""Invoice-side tests for custom fields: create/update payloads, list filter,
and detail response shape. Mirrors opportunity/tests/test_custom_fields.py.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.db import connection

from accounts.models import Account
from common.models import CustomFieldDefinition
from contacts.models import Contact
from invoices.models import Invoice

pg_only = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="JSONField __contains lookup requires PostgreSQL",
)


INVOICES_LIST_URL = "/api/invoices/"


def _set_rls(org):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.current_org', %s, false)", [str(org.id)]
        )


def _make_priority_def(org, **overrides):
    defaults = {
        "target_model": "Invoice",
        "key": "billing_priority",
        "label": "Billing Priority",
        "field_type": "dropdown",
        "options": [
            {"value": "standard", "label": "Standard"},
            {"value": "rush", "label": "Rush"},
        ],
        "is_required": False,
        "is_active": True,
    }
    defaults.update(overrides)
    return CustomFieldDefinition.objects.create(org=org, **defaults)


@pytest.fixture
def cf_account(org_a):
    _set_rls(org_a)
    return Account.objects.create(name="CF Invoice Account", org=org_a)


@pytest.fixture
def cf_contact(org_a):
    _set_rls(org_a)
    return Contact.objects.create(
        first_name="CF",
        last_name="Contact",
        email="cf-contact@example.com",
        org=org_a,
    )


@pytest.fixture
def cf_invoice(org_a, cf_account):
    _set_rls(org_a)
    return Invoice.objects.create(
        invoice_title="Primary CF Invoice",
        account=cf_account,
        currency="USD",
        org=org_a,
    )


@pytest.fixture
def cf_invoice_secondary(org_a, cf_account):
    _set_rls(org_a)
    return Invoice.objects.create(
        invoice_title="Secondary CF Invoice",
        account=cf_account,
        currency="USD",
        org=org_a,
    )


@pytest.mark.django_db
class TestInvoiceCreateWithCustomFields:
    @patch("invoices.api_views.create_invoice_history.delay")
    def test_create_with_valid_dropdown_value(
        self, _history, admin_client, org_a, cf_account, cf_contact
    ):
        _make_priority_def(org_a)
        response = admin_client.post(
            INVOICES_LIST_URL,
            {
                "invoice_title": "Rush Invoice",
                "account_id": str(cf_account.id),
                "contact_id": str(cf_contact.id),
                "currency": "USD",
                "custom_fields": {"billing_priority": "rush"},
            },
            format="json",
        )
        assert response.status_code == 201, response.content
        inv = Invoice.objects.get(invoice_title="Rush Invoice", org=org_a)
        assert inv.custom_fields == {"billing_priority": "rush"}

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_create_rejects_invalid_dropdown_value(
        self, _history, admin_client, org_a, cf_account, cf_contact
    ):
        _make_priority_def(org_a)
        response = admin_client.post(
            INVOICES_LIST_URL,
            {
                "invoice_title": "Bad Priority Invoice",
                "account_id": str(cf_account.id),
                "contact_id": str(cf_contact.id),
                "currency": "USD",
                "custom_fields": {"billing_priority": "platinum"},
            },
            format="json",
        )
        assert response.status_code == 400
        body = response.json()
        assert "custom_fields" in body["errors"]
        assert "billing_priority" in body["errors"]["custom_fields"]

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_create_drops_unknown_keys(
        self, _history, admin_client, org_a, cf_account, cf_contact
    ):
        _make_priority_def(org_a)
        response = admin_client.post(
            INVOICES_LIST_URL,
            {
                "invoice_title": "Unknown CF Invoice",
                "account_id": str(cf_account.id),
                "contact_id": str(cf_contact.id),
                "currency": "USD",
                "custom_fields": {
                    "billing_priority": "standard",
                    "ghost": "ignored",
                },
            },
            format="json",
        )
        assert response.status_code == 201
        inv = Invoice.objects.get(invoice_title="Unknown CF Invoice", org=org_a)
        assert inv.custom_fields == {"billing_priority": "standard"}

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_create_required_missing_returns_400(
        self, _history, admin_client, org_a, cf_account, cf_contact
    ):
        _make_priority_def(org_a, is_required=True)
        response = admin_client.post(
            INVOICES_LIST_URL,
            {
                "invoice_title": "No CF Invoice",
                "account_id": str(cf_account.id),
                "contact_id": str(cf_contact.id),
                "currency": "USD",
            },
            format="json",
        )
        assert response.status_code == 400
        assert "billing_priority" in response.json()["errors"]["custom_fields"]


@pytest.mark.django_db
class TestInvoiceUpdateWithCustomFields:
    @patch("invoices.api_views.create_invoice_history.delay")
    def test_put_partial_merges_with_existing(
        self, _history, admin_client, cf_invoice, org_a
    ):
        _make_priority_def(org_a)
        _make_priority_def(
            org_a,
            key="po_reference",
            field_type="text",
            options=None,
        )
        cf_invoice.custom_fields = {"billing_priority": "rush"}
        cf_invoice.save()

        response = admin_client.put(
            f"{INVOICES_LIST_URL}{cf_invoice.id}/",
            {"custom_fields": {"po_reference": "PO-9000"}},
            format="json",
        )
        assert response.status_code == 200, response.content
        cf_invoice.refresh_from_db()
        assert cf_invoice.custom_fields == {
            "billing_priority": "rush",
            "po_reference": "PO-9000",
        }

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_put_invalid_returns_400(self, _history, admin_client, cf_invoice, org_a):
        _make_priority_def(org_a)
        response = admin_client.put(
            f"{INVOICES_LIST_URL}{cf_invoice.id}/",
            {"custom_fields": {"billing_priority": "platinum"}},
            format="json",
        )
        assert response.status_code == 400

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_put_without_custom_fields_preserves_existing(
        self, _history, admin_client, cf_invoice, org_a
    ):
        _make_priority_def(org_a)
        cf_invoice.custom_fields = {"billing_priority": "standard"}
        cf_invoice.save()

        response = admin_client.put(
            f"{INVOICES_LIST_URL}{cf_invoice.id}/",
            {"invoice_title": "Renamed Invoice"},
            format="json",
        )
        assert response.status_code == 200, response.content
        cf_invoice.refresh_from_db()
        assert cf_invoice.custom_fields == {"billing_priority": "standard"}


@pg_only
@pytest.mark.django_db
class TestInvoiceListFilter:
    def test_cf_filter_returns_matching(
        self, admin_client, cf_invoice, cf_invoice_secondary, org_a
    ):
        _make_priority_def(org_a)
        cf_invoice.custom_fields = {"billing_priority": "rush"}
        cf_invoice.save()
        cf_invoice_secondary.custom_fields = {"billing_priority": "standard"}
        cf_invoice_secondary.save()

        response = admin_client.get(
            f"{INVOICES_LIST_URL}?cf_billing_priority=rush"
        )
        ids = [r["id"] for r in response.json()["results"]]
        assert str(cf_invoice.id) in ids
        assert str(cf_invoice_secondary.id) not in ids


@pytest.mark.django_db
class TestInvoiceDetailResponse:
    def test_detail_includes_definitions_and_values(
        self, admin_client, cf_invoice, org_a
    ):
        _make_priority_def(org_a)
        cf_invoice.custom_fields = {"billing_priority": "standard"}
        cf_invoice.save()

        response = admin_client.get(f"{INVOICES_LIST_URL}{cf_invoice.id}/")
        assert response.status_code == 200, response.content
        body = response.json()
        assert body["invoice"]["custom_fields"] == {"billing_priority": "standard"}
        keys = [d["key"] for d in body["custom_field_definitions"]]
        assert "billing_priority" in keys

    def test_detail_excludes_inactive_definitions(
        self, admin_client, cf_invoice, org_a
    ):
        _make_priority_def(org_a)
        _make_priority_def(
            org_a, key="legacy", field_type="text", options=None, is_active=False
        )
        response = admin_client.get(f"{INVOICES_LIST_URL}{cf_invoice.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "billing_priority" in keys
        assert "legacy" not in keys

    def test_cross_org_does_not_leak_definitions(
        self, admin_client, cf_invoice, org_a, org_b
    ):
        CustomFieldDefinition.objects.create(
            org=org_b,
            target_model="Invoice",
            key="other_org_field",
            label="Other org",
            field_type="text",
        )
        response = admin_client.get(f"{INVOICES_LIST_URL}{cf_invoice.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "other_org_field" not in keys
