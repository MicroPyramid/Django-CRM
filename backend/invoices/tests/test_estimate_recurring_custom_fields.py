"""Custom-field tests for Estimate and RecurringInvoice. Mirrors the
invoices/tests/test_custom_fields.py pattern.
"""

from __future__ import annotations

import datetime

import pytest
from django.db import connection

from accounts.models import Account
from common.models import CustomFieldDefinition
from contacts.models import Contact
from invoices.models import Estimate, RecurringInvoice

pg_only = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="JSONField __contains lookup requires PostgreSQL",
)


ESTIMATES_URL = "/api/invoices/estimates/"
RECURRING_URL = "/api/invoices/recurring/"


def _set_rls(org):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.current_org', %s, false)", [str(org.id)]
        )


def _make_def(org, target_model, **overrides):
    defaults = {
        "target_model": target_model,
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
    return Account.objects.create(name="CF Doc Account", org=org_a)


@pytest.fixture
def cf_contact(org_a):
    _set_rls(org_a)
    return Contact.objects.create(
        first_name="CF",
        last_name="Doc",
        email="cf-doc@example.com",
        org=org_a,
    )


# ---------------------------------------------------------------------------
# Estimate
# ---------------------------------------------------------------------------


@pytest.fixture
def cf_estimate(org_a, cf_account, cf_contact):
    _set_rls(org_a)
    return Estimate.objects.create(
        title="Primary Estimate",
        account=cf_account,
        contact=cf_contact,
        client_name="Client",
        client_email="client@example.com",
        currency="USD",
        issue_date=datetime.date.today(),
        expiry_date=datetime.date.today() + datetime.timedelta(days=30),
        org=org_a,
    )


@pytest.fixture
def cf_estimate_secondary(org_a, cf_account, cf_contact):
    _set_rls(org_a)
    return Estimate.objects.create(
        title="Secondary Estimate",
        account=cf_account,
        contact=cf_contact,
        client_name="Client",
        client_email="client@example.com",
        currency="USD",
        issue_date=datetime.date.today(),
        expiry_date=datetime.date.today() + datetime.timedelta(days=30),
        org=org_a,
    )


@pytest.mark.django_db
class TestEstimateCreateWithCustomFields:
    def test_create_with_valid_dropdown_value(
        self, admin_client, org_a, cf_account, cf_contact
    ):
        _make_def(org_a, "Estimate")
        response = admin_client.post(
            ESTIMATES_URL,
            {
                "title": "Rush Estimate",
                "account_id": str(cf_account.id),
                "contact_id": str(cf_contact.id),
                "currency": "USD",
                "issue_date": str(datetime.date.today()),
                "expiry_date": str(datetime.date.today() + datetime.timedelta(days=30)),
                "custom_fields": {"billing_priority": "rush"},
            },
            format="json",
        )
        assert response.status_code == 201, response.content
        est = Estimate.objects.get(title="Rush Estimate", org=org_a)
        assert est.custom_fields == {"billing_priority": "rush"}

    def test_create_rejects_invalid_dropdown(
        self, admin_client, org_a, cf_account, cf_contact
    ):
        _make_def(org_a, "Estimate")
        response = admin_client.post(
            ESTIMATES_URL,
            {
                "title": "Bad Tier Estimate",
                "account_id": str(cf_account.id),
                "contact_id": str(cf_contact.id),
                "currency": "USD",
                "issue_date": str(datetime.date.today()),
                "expiry_date": str(datetime.date.today() + datetime.timedelta(days=30)),
                "custom_fields": {"billing_priority": "platinum"},
            },
            format="json",
        )
        assert response.status_code == 400
        assert "billing_priority" in response.json()["errors"]["custom_fields"]


@pytest.mark.django_db
class TestEstimateUpdateWithCustomFields:
    def test_put_partial_merges(self, admin_client, cf_estimate, org_a):
        _make_def(org_a, "Estimate")
        _make_def(
            org_a,
            "Estimate",
            key="reference_code",
            field_type="text",
            options=None,
        )
        cf_estimate.custom_fields = {"billing_priority": "rush"}
        cf_estimate.save()

        response = admin_client.put(
            f"{ESTIMATES_URL}{cf_estimate.id}/",
            {"custom_fields": {"reference_code": "REF-9000"}},
            format="json",
        )
        assert response.status_code == 200, response.content
        cf_estimate.refresh_from_db()
        assert cf_estimate.custom_fields == {
            "billing_priority": "rush",
            "reference_code": "REF-9000",
        }

    def test_put_invalid_returns_400(self, admin_client, cf_estimate, org_a):
        _make_def(org_a, "Estimate")
        response = admin_client.put(
            f"{ESTIMATES_URL}{cf_estimate.id}/",
            {"custom_fields": {"billing_priority": "platinum"}},
            format="json",
        )
        assert response.status_code == 400


@pg_only
@pytest.mark.django_db
class TestEstimateListFilter:
    def test_cf_filter_returns_matching(
        self, admin_client, cf_estimate, cf_estimate_secondary, org_a
    ):
        _make_def(org_a, "Estimate")
        cf_estimate.custom_fields = {"billing_priority": "rush"}
        cf_estimate.save()
        cf_estimate_secondary.custom_fields = {"billing_priority": "standard"}
        cf_estimate_secondary.save()

        response = admin_client.get(f"{ESTIMATES_URL}?cf_billing_priority=rush")
        ids = [r["id"] for r in response.json()["results"]]
        assert str(cf_estimate.id) in ids
        assert str(cf_estimate_secondary.id) not in ids


@pytest.mark.django_db
class TestEstimateDetailResponse:
    def test_detail_includes_definitions_and_values(
        self, admin_client, cf_estimate, org_a
    ):
        _make_def(org_a, "Estimate")
        cf_estimate.custom_fields = {"billing_priority": "standard"}
        cf_estimate.save()

        response = admin_client.get(f"{ESTIMATES_URL}{cf_estimate.id}/")
        assert response.status_code == 200, response.content
        body = response.json()
        assert body["estimate"]["custom_fields"] == {"billing_priority": "standard"}
        keys = [d["key"] for d in body["custom_field_definitions"]]
        assert "billing_priority" in keys

    def test_cross_org_does_not_leak_definitions(
        self, admin_client, cf_estimate, org_a, org_b
    ):
        CustomFieldDefinition.objects.create(
            org=org_b,
            target_model="Estimate",
            key="other_org_field",
            label="Other org",
            field_type="text",
        )
        response = admin_client.get(f"{ESTIMATES_URL}{cf_estimate.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "other_org_field" not in keys


# ---------------------------------------------------------------------------
# RecurringInvoice
# ---------------------------------------------------------------------------


@pytest.fixture
def cf_recurring(org_a, cf_account, cf_contact):
    _set_rls(org_a)
    return RecurringInvoice.objects.create(
        title="Primary Recurring",
        account=cf_account,
        contact=cf_contact,
        client_name="Client",
        client_email="client@example.com",
        frequency="MONTHLY",
        start_date=datetime.date.today(),
        next_generation_date=datetime.date.today(),
        payment_terms="NET_30",
        currency="USD",
        is_active=True,
        org=org_a,
    )


@pytest.fixture
def cf_recurring_secondary(org_a, cf_account, cf_contact):
    _set_rls(org_a)
    return RecurringInvoice.objects.create(
        title="Secondary Recurring",
        account=cf_account,
        contact=cf_contact,
        client_name="Client",
        client_email="client@example.com",
        frequency="MONTHLY",
        start_date=datetime.date.today(),
        next_generation_date=datetime.date.today(),
        payment_terms="NET_30",
        currency="USD",
        is_active=True,
        org=org_a,
    )


@pytest.mark.django_db
class TestRecurringCreateWithCustomFields:
    def test_create_with_valid_dropdown_value(
        self, admin_client, org_a, cf_account, cf_contact
    ):
        _make_def(org_a, "RecurringInvoice")
        response = admin_client.post(
            RECURRING_URL,
            {
                "title": "Rush Recurring",
                "account_id": str(cf_account.id),
                "contact_id": str(cf_contact.id),
                "frequency": "MONTHLY",
                "start_date": str(datetime.date.today()),
                "next_generation_date": str(datetime.date.today()),
                "payment_terms": "NET_30",
                "currency": "USD",
                "is_active": True,
                "custom_fields": {"billing_priority": "rush"},
            },
            format="json",
        )
        assert response.status_code == 201, response.content
        rec = RecurringInvoice.objects.get(title="Rush Recurring", org=org_a)
        assert rec.custom_fields == {"billing_priority": "rush"}

    def test_create_rejects_invalid_dropdown(
        self, admin_client, org_a, cf_account, cf_contact
    ):
        _make_def(org_a, "RecurringInvoice")
        response = admin_client.post(
            RECURRING_URL,
            {
                "title": "Bad Recurring",
                "account_id": str(cf_account.id),
                "contact_id": str(cf_contact.id),
                "frequency": "MONTHLY",
                "start_date": str(datetime.date.today()),
                "next_generation_date": str(datetime.date.today()),
                "payment_terms": "NET_30",
                "currency": "USD",
                "is_active": True,
                "custom_fields": {"billing_priority": "platinum"},
            },
            format="json",
        )
        assert response.status_code == 400
        assert "billing_priority" in response.json()["errors"]["custom_fields"]


@pytest.mark.django_db
class TestRecurringUpdateWithCustomFields:
    def test_put_partial_merges(self, admin_client, cf_recurring, org_a):
        _make_def(org_a, "RecurringInvoice")
        _make_def(
            org_a,
            "RecurringInvoice",
            key="reference_code",
            field_type="text",
            options=None,
        )
        cf_recurring.custom_fields = {"billing_priority": "rush"}
        cf_recurring.save()

        response = admin_client.put(
            f"{RECURRING_URL}{cf_recurring.id}/",
            {"custom_fields": {"reference_code": "REF-9000"}},
            format="json",
        )
        assert response.status_code == 200, response.content
        cf_recurring.refresh_from_db()
        assert cf_recurring.custom_fields == {
            "billing_priority": "rush",
            "reference_code": "REF-9000",
        }


@pg_only
@pytest.mark.django_db
class TestRecurringListFilter:
    def test_cf_filter_returns_matching(
        self, admin_client, cf_recurring, cf_recurring_secondary, org_a
    ):
        _make_def(org_a, "RecurringInvoice")
        cf_recurring.custom_fields = {"billing_priority": "rush"}
        cf_recurring.save()
        cf_recurring_secondary.custom_fields = {"billing_priority": "standard"}
        cf_recurring_secondary.save()

        response = admin_client.get(f"{RECURRING_URL}?cf_billing_priority=rush")
        ids = [r["id"] for r in response.json()["results"]]
        assert str(cf_recurring.id) in ids
        assert str(cf_recurring_secondary.id) not in ids


@pytest.mark.django_db
class TestRecurringDetailResponse:
    def test_detail_includes_definitions_and_values(
        self, admin_client, cf_recurring, org_a
    ):
        _make_def(org_a, "RecurringInvoice")
        cf_recurring.custom_fields = {"billing_priority": "standard"}
        cf_recurring.save()

        response = admin_client.get(f"{RECURRING_URL}{cf_recurring.id}/")
        assert response.status_code == 200, response.content
        body = response.json()
        assert body["recurring_invoice"]["custom_fields"] == {
            "billing_priority": "standard"
        }
        keys = [d["key"] for d in body["custom_field_definitions"]]
        assert "billing_priority" in keys

    def test_cross_org_does_not_leak_definitions(
        self, admin_client, cf_recurring, org_a, org_b
    ):
        CustomFieldDefinition.objects.create(
            org=org_b,
            target_model="RecurringInvoice",
            key="other_org_field",
            label="Other org",
            field_type="text",
        )
        response = admin_client.get(f"{RECURRING_URL}{cf_recurring.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "other_org_field" not in keys
