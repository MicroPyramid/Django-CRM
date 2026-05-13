"""Accounts-side tests for custom fields: Account create/update payloads, list
filter, and detail-page response shape.

Mirrors leads/tests/test_custom_fields.py.
"""

from __future__ import annotations

import pytest
from django.db import connection

from accounts.models import Account
from common.models import CustomFieldDefinition

pg_only = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="JSONField __contains lookup requires PostgreSQL",
)


ACCOUNTS_LIST_URL = "/api/accounts/"


def _set_rls(org):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.current_org', %s, false)", [str(org.id)]
        )


def _make_tier_def(org, **overrides):
    defaults = {
        "target_model": "Account",
        "key": "tier",
        "label": "Tier",
        "field_type": "dropdown",
        "options": [
            {"value": "gold", "label": "Gold"},
            {"value": "silver", "label": "Silver"},
        ],
        "is_required": False,
        "is_active": True,
    }
    defaults.update(overrides)
    return CustomFieldDefinition.objects.create(org=org, **defaults)


@pytest.fixture
def account_a(org_a):
    _set_rls(org_a)
    return Account.objects.create(name="Acme Corp", org=org_a)


@pytest.fixture
def account_a2(org_a):
    _set_rls(org_a)
    return Account.objects.create(name="Globex", org=org_a)


@pytest.mark.django_db
class TestAccountCreateWithCustomFields:
    def test_create_with_valid_dropdown_value(self, admin_client, org_a):
        _make_tier_def(org_a)
        response = admin_client.post(
            ACCOUNTS_LIST_URL,
            {"name": "Tiered Co", "custom_fields": {"tier": "gold"}},
            format="json",
        )
        assert response.status_code == 200, response.content
        account = Account.objects.get(name="Tiered Co", org=org_a)
        assert account.custom_fields == {"tier": "gold"}

    def test_create_rejects_invalid_dropdown_value(self, admin_client, org_a):
        _make_tier_def(org_a)
        response = admin_client.post(
            ACCOUNTS_LIST_URL,
            {"name": "Bad Tier Co", "custom_fields": {"tier": "platinum"}},
            format="json",
        )
        assert response.status_code == 400
        assert "custom_fields" in response.json()["errors"]
        assert "tier" in response.json()["errors"]["custom_fields"]

    def test_create_drops_unknown_keys(self, admin_client, org_a):
        _make_tier_def(org_a)
        response = admin_client.post(
            ACCOUNTS_LIST_URL,
            {
                "name": "Unknown Key Co",
                "custom_fields": {"tier": "gold", "made_up": "ignored"},
            },
            format="json",
        )
        assert response.status_code == 200
        account = Account.objects.get(name="Unknown Key Co", org=org_a)
        assert account.custom_fields == {"tier": "gold"}

    def test_create_required_missing_returns_400(self, admin_client, org_a):
        _make_tier_def(org_a, is_required=True)
        response = admin_client.post(
            ACCOUNTS_LIST_URL,
            {"name": "No CF Co"},
            format="json",
        )
        assert response.status_code == 400
        assert "tier" in response.json()["errors"]["custom_fields"]


@pytest.mark.django_db
class TestAccountUpdateWithCustomFields:
    def test_patch_merges_with_existing(self, admin_client, account_a, org_a):
        _make_tier_def(org_a)
        _make_tier_def(
            org_a,
            key="employees_offsite",
            field_type="number",
            options=None,
        )
        account_a.custom_fields = {"tier": "gold"}
        account_a.save()

        response = admin_client.patch(
            f"{ACCOUNTS_LIST_URL}{account_a.id}/",
            {"custom_fields": {"employees_offsite": 12}},
            format="json",
        )
        assert response.status_code == 200, response.content
        account_a.refresh_from_db()
        assert account_a.custom_fields == {"tier": "gold", "employees_offsite": 12.0}

    def test_patch_invalid_returns_400(self, admin_client, account_a, org_a):
        _make_tier_def(org_a)
        response = admin_client.patch(
            f"{ACCOUNTS_LIST_URL}{account_a.id}/",
            {"custom_fields": {"tier": "platinum"}},
            format="json",
        )
        assert response.status_code == 400

    def test_put_replaces_custom_fields(self, admin_client, account_a, org_a):
        _make_tier_def(org_a)
        account_a.custom_fields = {"tier": "silver"}
        account_a.save()

        response = admin_client.put(
            f"{ACCOUNTS_LIST_URL}{account_a.id}/",
            {"name": account_a.name, "custom_fields": {"tier": "gold"}},
            format="json",
        )
        assert response.status_code == 200, response.content
        account_a.refresh_from_db()
        assert account_a.custom_fields == {"tier": "gold"}


@pg_only
@pytest.mark.django_db
class TestAccountListFilter:
    def test_cf_filter_returns_matching(
        self, admin_client, account_a, account_a2, org_a
    ):
        _make_tier_def(org_a)
        account_a.custom_fields = {"tier": "gold"}
        account_a.save()
        account_a2.custom_fields = {"tier": "silver"}
        account_a2.save()

        response = admin_client.get(f"{ACCOUNTS_LIST_URL}?cf_tier=gold")
        body = response.json()
        ids = [a["id"] for a in body["active_accounts"]["open_accounts"]]
        assert str(account_a.id) in ids
        assert str(account_a2.id) not in ids


@pytest.mark.django_db
class TestAccountDetailResponse:
    def test_detail_includes_definitions_and_values(
        self, admin_client, account_a, org_a
    ):
        _make_tier_def(org_a)
        account_a.custom_fields = {"tier": "silver"}
        account_a.save()

        response = admin_client.get(f"{ACCOUNTS_LIST_URL}{account_a.id}/")
        assert response.status_code == 200, response.content
        body = response.json()
        assert body["account_obj"]["custom_fields"] == {"tier": "silver"}
        keys = [d["key"] for d in body["custom_field_definitions"]]
        assert "tier" in keys

    def test_detail_excludes_inactive_definitions(
        self, admin_client, account_a, org_a
    ):
        _make_tier_def(org_a)
        _make_tier_def(
            org_a, key="legacy", field_type="text", options=None, is_active=False
        )
        response = admin_client.get(f"{ACCOUNTS_LIST_URL}{account_a.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "tier" in keys
        assert "legacy" not in keys

    def test_cross_org_does_not_leak_definitions(
        self, admin_client, account_a, org_a, org_b
    ):
        CustomFieldDefinition.objects.create(
            org=org_b,
            target_model="Account",
            key="other_org_field",
            label="Other org",
            field_type="text",
        )
        response = admin_client.get(f"{ACCOUNTS_LIST_URL}{account_a.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "other_org_field" not in keys
