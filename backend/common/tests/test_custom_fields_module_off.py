"""Custom-field targets follow their module: an off module's fields leave the
list and its totals, refuse a new definition, and answer not found."""

import pytest

from cases.models import Case
from common.models import CustomFieldDefinition
from common.testing import set_modules_off

URL = "/api/custom-fields/"
OFF = "Tickets is switched off for this organization."


@pytest.fixture
def two_fields(org_a):
    ticket = CustomFieldDefinition.objects.create(
        org=org_a, target_model="Case", key="sev", label="Sev", field_type="text"
    )
    lead = CustomFieldDefinition.objects.create(
        org=org_a, target_model="Lead", key="src", label="Src", field_type="text"
    )
    return ticket, lead


def _payload(**overrides):
    body = {
        "target_model": "Case",
        "key": "tier",
        "label": "Tier",
        "field_type": "text",
    }
    return {**body, **overrides}


def test_the_list_leaves_out_off_module_targets(admin_client, org_a, two_fields):
    ticket, lead = two_fields
    Case.objects.create(name="One", org=org_a, status="New")
    body = admin_client.get(URL).json()
    assert {d["key"] for d in body["definitions"]} == {"sev", "src"}
    assert body["totals"]["count"] == 2
    assert body["totals"]["models_extended"] == 2

    set_modules_off(org_a, "tickets")
    body = admin_client.get(URL).json()
    assert [d["key"] for d in body["definitions"]] == ["src"]
    assert body["totals"]["count"] == 1
    assert body["totals"]["models_extended"] == 1
    assert str(ticket.id) not in {d["id"] for d in body["definitions"]}
    assert admin_client.get(URL, {"target_model": "Case"}).json()["definitions"] == []


def test_the_counts_never_touch_an_off_target(
    admin_client, org_a, two_fields, monkeypatch
):
    from common.views import custom_field_views

    seen = []
    real = custom_field_views._records_missing_map

    def spy(org, definitions):
        seen.extend(d.target_model for d in definitions)
        return real(org, definitions)

    monkeypatch.setattr(custom_field_views, "_records_missing_map", spy)
    set_modules_off(org_a, "tickets")
    admin_client.get(URL)
    assert seen == ["Lead"]


def test_creating_a_field_on_an_off_module_is_refused(admin_client, org_a):
    ok = admin_client.post(URL, _payload(), format="json")
    assert ok.status_code == 201
    set_modules_off(org_a, "tickets")
    refused = admin_client.post(URL, _payload(key="tier2"), format="json")
    assert refused.status_code == 400
    assert OFF in refused.json()["errors"]["target_model"]
    assert not CustomFieldDefinition.objects.filter(key="tier2").exists()
    assert (
        admin_client.post(URL, _payload(target_model="Lead"), format="json").status_code
        == 201
    )


def test_a_member_still_cannot_create(user_client, org_a):
    set_modules_off(org_a, "tickets")
    assert user_client.post(URL, _payload(), format="json").status_code == 403


def test_an_off_module_field_answers_not_found(admin_client, org_a, two_fields):
    ticket, _ = two_fields
    url = f"{URL}{ticket.id}/"
    assert admin_client.get(url).status_code == 200
    set_modules_off(org_a, "tickets")
    for response in (
        admin_client.get(url),
        admin_client.put(url, {"label": "New"}, format="json"),
        admin_client.delete(url),
    ):
        assert response.status_code == 404
        assert response.json()["errors"] == "Custom field not found"
    ticket.refresh_from_db()
    assert (ticket.label, ticket.is_active) == ("Sev", True)
    set_modules_off(org_a)
    assert admin_client.get(url).status_code == 200
