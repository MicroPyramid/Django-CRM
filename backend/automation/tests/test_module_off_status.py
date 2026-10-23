"""A rule on an off module shows Paused, does not run, and changes nothing else."""

import pytest
from django.utils import timezone

from automation import plan
from automation.models import AutomationRule, AutomationRun
from automation.plan import Runnable
from cases.models import Case
from common.testing import set_modules_off

RULES = "/api/automation/rules/"
PAUSED = "Paused: Tickets is switched off"
OFF = "Tickets is switched off for this organization."
CREATED = {"event": "created", "field": None, "to": None}
SET_PRIORITY = {
    "type": "set_field",
    "target": "record",
    "field": "priority",
    "value": "Urgent",
}
LEAD_NOTE = {"type": "notify", "to": ["admins"], "people": [], "message": "New lead"}


@pytest.fixture(autouse=True)
def fresh_plan_hooks():
    saved = list(plan._HOOKS)
    yield
    plan._HOOKS[:] = saved


@pytest.fixture
def commit(django_capture_on_commit_callbacks):
    return lambda: django_capture_on_commit_callbacks(execute=True)


def _rule(org, owner, object_key, name, actions=None):
    return AutomationRule.objects.create(
        org=org,
        name=name,
        object_key=object_key,
        trigger=dict(CREATED),
        conditions=[],
        actions=actions or [dict(SET_PRIORITY)],
        owner=owner,
        is_active=True,
        switched_on_at=timezone.now(),
    )


def _by_name(client):
    return {r["name"]: r for r in client.get(RULES).json()["results"]}


def _ticket(org):
    return Case.objects.create(org=org, name="Login bug", status="New", priority="Low")


@pytest.fixture
def rules(org_a, admin_profile):
    return (
        _rule(org_a, admin_profile, "ticket", "Ticket rule"),
        _rule(org_a, admin_profile, "lead", "Lead rule", [LEAD_NOTE]),
    )


def test_a_rule_on_an_off_module_shows_paused(admin_client, org_a, rules):
    assert _by_name(admin_client)["Ticket rule"]["status"] == "on"

    set_modules_off(org_a, "tickets")

    listed = _by_name(admin_client)
    assert listed["Ticket rule"]["status"] == "paused"
    assert listed["Ticket rule"]["status_text"] == PAUSED
    assert listed["Lead rule"]["status"] == "on"


def test_a_paused_rule_does_not_run(org_a, rules, commit):
    set_modules_off(org_a, "tickets")

    with commit():
        ticket = _ticket(org_a)

    ticket.refresh_from_db()
    assert ticket.priority == "Low"
    assert not AutomationRun.objects.filter(org=org_a).exists()


def test_pausing_by_module_changes_nothing_on_the_rule(admin_client, org_a, rules):
    ticket_rule, _ = rules
    before = (
        ticket_rule.is_active,
        ticket_rule.switched_on_at,
        ticket_rule.paused_reason,
    )
    asked = []

    class Spy:
        def runnable(self, org, given):
            asked.append([r.id for r in given])
            return Runnable(frozenset(r.id for r in given), {}, None)

        def may_switch_on(self, org, rule):
            return None

    plan._HOOKS[:] = [Spy()]
    set_modules_off(org_a, "tickets")

    assert _by_name(admin_client)["Ticket rule"]["status"] == "paused"

    assert ticket_rule.id in asked[0]
    ticket_rule.refresh_from_db()
    assert (
        ticket_rule.is_active,
        ticket_rule.switched_on_at,
        ticket_rule.paused_reason,
    ) == before


def test_switching_the_module_on_resumes_the_rule(admin_client, org_a, rules, commit):
    set_modules_off(org_a, "tickets")
    assert _by_name(admin_client)["Ticket rule"]["status"] == "paused"

    set_modules_off(org_a)
    assert _by_name(admin_client)["Ticket rule"]["status"] == "on"

    with commit():
        ticket = _ticket(org_a)
    ticket.refresh_from_db()
    assert ticket.priority == "Urgent"
    assert AutomationRun.objects.filter(org=org_a, object_key="ticket").exists()


def test_saving_a_rule_on_an_off_module_names_the_module(admin_client, org_a, rules):
    ticket_rule, _ = rules
    set_modules_off(org_a, "tickets")

    response = admin_client.patch(
        f"{RULES}{ticket_rule.id}/",
        {"trigger": {"event": "updated", "field": "name", "to": None}},
        format="json",
    )

    assert response.status_code == 400
    assert response.json() == {"errors": {"object_key": [OFF]}}


def test_the_catalogue_leaves_out_off_module_objects(admin_client, org_a):
    def keys():
        body = admin_client.get("/api/automation/catalogue/").json()
        return {o["key"] for o in body["objects"]}

    assert "ticket" in keys()
    set_modules_off(org_a, "tickets")
    assert "ticket" not in keys()
    assert "lead" in keys()


def test_switching_on_a_rule_on_an_off_module_is_allowed(admin_client, org_a, rules):
    ticket_rule, _ = rules
    ticket_rule.is_active = False
    ticket_rule.save(update_fields=["is_active"])
    set_modules_off(org_a, "tickets")

    response = admin_client.patch(
        f"{RULES}{ticket_rule.id}/", {"is_active": True}, format="json"
    )

    assert response.status_code == 200, response.content
    ticket_rule.refresh_from_db()
    assert ticket_rule.is_active is True
    listed = _by_name(admin_client)["Ticket rule"]
    assert (listed["status"], listed["status_text"]) == ("paused", PAUSED)


def test_creating_a_rule_on_an_off_module_names_the_module(admin_client, org_a):
    set_modules_off(org_a, "tickets")
    body = {
        "name": "New",
        "object_key": "ticket",
        "trigger": dict(CREATED),
        "match": "all",
        "conditions": [],
        "actions": [dict(SET_PRIORITY)],
    }

    response = admin_client.post(RULES, body, format="json")

    assert response.status_code == 400
    assert response.json() == {"errors": {"object_key": [OFF]}}
    assert not AutomationRule.objects.filter(org=org_a, name="New").exists()


@pytest.mark.parametrize(
    "change",
    [
        {"conditions": [{"field": "name", "op": "eq", "value": "x"}]},
        {"is_active": True, "actions": [{"type": "bogus"}]},
    ],
)
def test_editing_the_rule_fields_of_a_parked_rule_is_refused(
    admin_client, org_a, rules, change
):
    ticket_rule, _ = rules
    set_modules_off(org_a, "tickets")

    response = admin_client.patch(f"{RULES}{ticket_rule.id}/", change, format="json")

    assert response.status_code == 400
    assert response.json() == {"errors": {"object_key": [OFF]}}
    ticket_rule.refresh_from_db()
    assert ticket_rule.actions == [SET_PRIORITY]
