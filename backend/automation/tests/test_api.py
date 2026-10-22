"""The automation admin API: who may use it, what it takes and what it answers."""

import uuid
from datetime import timedelta

import pytest
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.test import APIClient

from automation import links, plan
from automation.links import LinkSpec, register_link_hook
from automation.models import DONE, FAILED, SKIPPED, AutomationRule, AutomationRun
from automation.ownership import SENTENCES
from automation.plan import Runnable, register_plan_hook
from common.models import Notification, PersonalAccessToken, Profile, User
from common.testing import _make_authenticated_client
from conftest import rls_org
from leads.models import Lead
from opportunity.models import DealPipeline, Opportunity
from tasks.models import Task
from webhooks.models import SLACK, WebhookEndpoint

BASE = "/api/automation/"
RULES = f"{BASE}rules/"
NAME_CHANGES = {"event": "updated", "field": "name", "to": None}
CREATED = {"event": "created", "field": None, "to": None}
NOT_A_MEMBER = "Each person must be an active member of this org."
OVER = "Over your plan's limit"


@pytest.fixture(autouse=True)
def fresh_state():
    saved_plan, saved_links = list(plan._HOOKS), list(links._HOOKS)
    cache.clear()
    yield
    plan._HOOKS[:] = saved_plan
    links._HOOKS[:] = saved_links


@pytest.fixture
def owner(admin_profile):
    admin_profile.user.name = "Olga"
    admin_profile.user.save(update_fields=["name"])
    return admin_profile


@pytest.fixture
def rule(org_a):
    return _rule(org_a)


@pytest.fixture
def deal(org_a):
    return _deal(org_a)


def _member(org, name, *, role="USER"):
    user = User.objects.create_user(
        email=f"{name.lower()}@example.com", password="testpass123", name=name
    )
    return Profile.objects.create(user=user, org=org, role=role, is_active=True)


def _client(profile):
    return _make_authenticated_client(profile.user, profile.org, profile)


def _deal(org, name="Acme renewal"):
    return Opportunity.objects.create(
        org=org,
        name=name,
        pipeline=DealPipeline.default_for(org),
        stage="QUALIFICATION",
    )


def _set(field, value):
    return {"type": "set_field", "target": "record", "field": field, "value": value}


def _task(assign_to="owner"):
    return {
        "type": "create_task",
        "title": "Call {name}",
        "due_in_days": None,
        "priority": "High",
        "assign_to": assign_to,
        "person": None,
    }


def _body(**fields):
    return {
        "name": "Deal rule",
        "object_key": "deal",
        "trigger": NAME_CHANGES,
        "match": "all",
        "conditions": [],
        "actions": [_set("probability", 30)],
        **fields,
    }


def _rule(org, *, owner=None, is_active=False, position=0, **fields):
    return AutomationRule.objects.create(
        org=org,
        owner=owner,
        is_active=is_active,
        position=position,
        switched_on_at=timezone.now() if is_active else None,
        **_body(**fields),
    )


def _run(rule, status=DONE, *, days_ago=0, **extra):
    run = AutomationRun.objects.create(
        org=rule.org,
        rule=rule,
        object_key=rule.object_key,
        record_id=uuid.uuid4(),
        record_name="Acme renewal",
        status=status,
        chain_id=uuid.uuid4(),
        **extra,
    )
    if days_ago:
        AutomationRun.objects.filter(pk=run.pk).update(
            created_at=timezone.now() - timedelta(days=days_ago)
        )
    return run


def _listed(client):
    return {r["name"]: r for r in client.get(RULES).json()["results"]}


class CapAtTwo:
    """Refuses a third active rule, as a registered hook might."""

    message = "This install allows 2 active automation rules."

    def may_switch_on(self, org, rule):
        others = AutomationRule.objects.filter(org=org, is_active=True)
        return self.message if others.exclude(pk=rule.pk).count() >= 2 else None

    def runnable(self, org, rules):
        return Runnable(frozenset(rule.id for rule in rules), {}, None)


class RefusesAll:
    """Refuses every switch-on, and notes each rule it was asked about."""

    message = "This install allows no more active automation rules."

    def __init__(self):
        self.asked = []

    def may_switch_on(self, org, rule):
        self.asked.append(rule.name)
        return self.message

    def runnable(self, org, rules):
        return Runnable(frozenset(rule.id for rule in rules), {}, None)


class FirstOnly:
    """Runs only the first active rule, and says why the rest do not."""

    def __init__(self):
        self.asked = []

    def may_switch_on(self, org, rule):
        return None

    def runnable(self, org, rules):
        self.asked.append([rule.name for rule in rules])
        first, *rest = rules
        return Runnable(
            frozenset({first.id}),
            {rule.id: OVER for rule in rest},
            "1 of 2 active rules run",
        )


class DealLinks:
    def specs(self, org, object_key):
        if object_key != "deal":
            return []
        return [
            LinkSpec("in:visits.deals", "Visits linked through Deals", "lead"),
            LinkSpec("in:gone.deals", "Gone linked through Deals", "obj:gone"),
        ]

    def records(self, org, object_key, record, spec_id):
        return []


# Who may use it

ROUTES = (
    "catalogue",
    "list",
    "create",
    "detail",
    "update",
    "delete",
    "try",
    "runs",
    "reorder",
)


def _route(name, rule, deal):
    """`(method, url, body, what an admin gets)` for one route."""
    one = f"{RULES}{rule.id}/"
    return {
        "catalogue": ("get", f"{BASE}catalogue/", None, 200),
        "list": ("get", RULES, None, 200),
        "create": ("post", RULES, _body(name="New rule"), 201),
        "detail": ("get", one, None, 200),
        "update": ("patch", one, {"name": "Renamed"}, 200),
        "delete": ("delete", one, None, 204),
        "try": ("post", f"{one}try/", {"record_id": str(deal.id)}, 200),
        "runs": ("get", f"{one}runs/", None, 200),
        "reorder": ("post", f"{RULES}reorder/", {"ids": [str(rule.id)]}, 200),
    }[name]


@pytest.mark.parametrize("name", ROUTES)
def test_a_member_is_refused(user_client, rule, deal, name):
    method, url, body, _ = _route(name, rule, deal)
    response = getattr(user_client, method)(url, body, format="json")
    assert response.status_code == 403, response.content
    assert list(AutomationRule.objects.values_list("name", flat=True)) == ["Deal rule"]


@pytest.mark.parametrize("name", ROUTES)
def test_an_admin_is_allowed(admin_client, rule, deal, name):
    method, url, body, expected = _route(name, rule, deal)
    response = getattr(admin_client, method)(url, body, format="json")
    assert response.status_code == expected, response.content


def test_an_admins_session_reaches_the_route_tokens_cannot(admin_client, admin_profile):
    """`test_tokens_cannot_reach_automation`'s 403 is the credential block's."""
    assert admin_client.get(RULES).status_code == 200
    raw, _ = PersonalAccessToken.generate(profile=admin_profile, name="cli")
    token = APIClient()
    token.credentials(HTTP_AUTHORIZATION=f"Bearer {raw}")
    assert token.get(RULES).status_code == 403


def test_another_orgs_rule_is_404(admin_client, org_b, deal):
    with rls_org(org_b):
        theirs = _rule(org_b, name="Their rule", is_active=True)
        _run(theirs)
    one = f"{RULES}{theirs.id}/"
    for method, url, body in (
        ("get", one, None),
        ("patch", one, {"name": "Mine now", "is_active": False}),
        ("delete", one, None),
        ("post", f"{one}try/", {"record_id": str(deal.id)}),
        ("get", f"{one}runs/", None),
    ):
        response = getattr(admin_client, method)(url, body, format="json")
        assert response.status_code == 404, (method, url)
    assert admin_client.get(RULES).json()["results"] == []
    with rls_org(org_b):
        theirs.refresh_from_db()
        assert AutomationRun.objects.filter(rule=theirs).count() == 1
    assert (theirs.name, theirs.is_active) == ("Their rule", True)


# Creating, listing and changing rules


def test_create_and_list(admin_client, org_a, org_b, owner):
    _rule(org_a, name="First", position=0)
    _rule(org_a, name="Second", position=4)
    ravi = _member(org_a, "Ravi", role="ADMIN")

    response = admin_client.post(
        RULES,
        _body(
            name="Won deals",
            position=0,
            owner=str(ravi.id),
            switched_on_at="2020-01-01T00:00:00Z",
            paused_reason="left",
            org=str(org_b.id),
        ),
        format="json",
    )

    assert response.status_code == 201, response.content
    created = response.json()
    rule = AutomationRule.objects.get(pk=created["id"])
    assert (rule.org_id, rule.position, rule.owner, rule.is_active) == (
        org_a.id,
        5,
        None,
        False,
    )
    assert (rule.switched_on_at, rule.paused_reason) == (None, "")
    assert (created["name"], created["owner"], created["position"]) == (
        "Won deals",
        None,
        5,
    )

    body = admin_client.get(RULES).json()
    assert body["summary"] is None
    assert [r["name"] for r in body["results"]] == ["First", "Second", "Won deals"]
    listed = body["results"][-1]
    assert listed == {
        **created,
        "status": "off",
        "status_text": "Off",
        "runs_7d": 0,
        "failures_7d": 0,
    }


def test_the_list_counts_the_last_seven_days_of_runs(admin_client, org_a):
    busy = _rule(org_a, name="Busy")
    _rule(org_a, name="Idle", position=1)
    _run(busy)
    _run(busy)
    _run(busy, FAILED, reason="actions[0].value: Enter a number.")
    _run(busy, FAILED, days_ago=8)
    _run(busy, SKIPPED, skipped_count=40, window_start=timezone.now())

    admin_client.get(RULES)
    with CaptureQueriesContext(connection) as two_rules:
        listed = _listed(admin_client)
    assert (listed["Busy"]["runs_7d"], listed["Busy"]["failures_7d"]) == (3, 1)
    assert (listed["Idle"]["runs_7d"], listed["Idle"]["failures_7d"]) == (0, 0)

    for n in range(3):
        _run(_rule(org_a, name=f"More {n}", position=2 + n), FAILED)
    with CaptureQueriesContext(connection) as five_rules:
        listed = _listed(admin_client)
    assert (listed["More 2"]["runs_7d"], listed["More 2"]["failures_7d"]) == (1, 1)
    assert len(five_rules) == len(two_rules)


def test_put_is_not_allowed(admin_client, rule):
    response = admin_client.put(
        f"{RULES}{rule.id}/", _body(name="Replaced"), format="json"
    )
    assert response.status_code == 405
    rule.refresh_from_db()
    assert rule.name == "Deal rule"


def test_an_invalid_rule_is_refused_with_paths(admin_client, org_a):
    response = admin_client.post(
        RULES,
        _body(
            conditions=[{"field": "probability", "op": "gt", "value": "lots"}],
            actions=[_set("probability", "lots"), {"type": "explode"}],
        ),
        format="json",
    )
    assert response.status_code == 400
    assert response.json() == {
        "errors": {
            "conditions[0].value": ["Enter a number."],
            "actions[0].value": ["Enter a number."],
            "actions[1].type": ["Unknown action."],
        }
    }

    response = admin_client.post(RULES, _body(name=""), format="json")
    assert response.status_code == 400
    assert list(response.json()["errors"]) == ["name"]
    assert not AutomationRule.objects.exists()

    # A PATCH is checked with the rest of the stored rule.
    stored = _rule(org_a, conditions=[{"field": "name", "op": "was", "value": "Acme"}])
    response = admin_client.patch(
        f"{RULES}{stored.id}/", {"trigger": CREATED}, format="json"
    )
    assert response.status_code == 400
    assert response.json() == {
        "errors": {"conditions[0].op": ["Only an updated trigger has an old value."]}
    }
    stored.refresh_from_db()
    assert stored.trigger == NAME_CHANGES


# Switching on and who owns a rule


def test_switching_on_sets_the_owner(admin_client, org_a, owner):
    before = timezone.now()
    response = admin_client.post(RULES, _body(is_active=True), format="json")
    assert response.status_code == 201, response.content
    assert response.json()["owner"] == {"id": str(owner.id), "name": "Olga"}
    created = AutomationRule.objects.get(pk=response.json()["id"])
    assert (created.owner, created.is_active) == (owner, True)
    assert created.switched_on_at >= before

    off = _rule(org_a, name="Off rule", position=1)
    # Read as the serializer reads it, so a string cannot skip the owner.
    worded = _rule(org_a, name="Worded", position=2)
    for target, value in ((off, True), (worded, "true")):
        response = admin_client.patch(
            f"{RULES}{target.id}/", {"is_active": value}, format="json"
        )
        assert response.status_code == 200, response.content
        target.refresh_from_db()
        assert (target.owner, target.is_active, target.paused_reason) == (
            owner,
            True,
            "",
        )
        assert target.switched_on_at >= before

    statuses = {
        name: (r["status"], r["status_text"])
        for name, r in _listed(admin_client).items()
    }
    assert statuses == {
        "Deal rule": ("on", "On"),
        "Off rule": ("on", "On"),
        "Worded": ("on", "On"),
    }


def test_another_admin_switching_a_paused_rule_on_takes_it_over(
    admin_client, org_a, owner
):
    ravi = _member(org_a, "Ravi", role="ADMIN")
    rule = _rule(org_a, owner=ravi, is_active=True)
    ravi.role = "USER"
    ravi.save()
    rule.refresh_from_db()
    assert (rule.is_active, rule.paused_reason) == (False, "not_admin")
    listed = _listed(admin_client)["Deal rule"]
    assert (listed["status"], listed["status_text"]) == (
        "paused",
        SENTENCES["not_admin"],
    )

    before = timezone.now()
    response = admin_client.patch(
        f"{RULES}{rule.id}/", {"is_active": True}, format="json"
    )

    assert response.status_code == 200, response.content
    assert response.json()["paused_reason"] == ""
    rule.refresh_from_db()
    assert (rule.owner, rule.is_active, rule.paused_reason) == (owner, True, "")
    assert rule.switched_on_at >= before
    assert _listed(admin_client)["Deal rule"]["status"] == "on"


def _demote(profile):
    Profile.objects.filter(pk=profile.pk).update(role="USER")


def _deactivate(profile):
    Profile.objects.filter(pk=profile.pk).update(is_active=False)


def _deactivate_user(profile):
    User.objects.filter(pk=profile.user_id).update(is_active=False)


@pytest.mark.parametrize(
    ("unseen", "sentence"),
    [
        (_demote, SENTENCES["not_admin"]),
        (_deactivate, SENTENCES["deactivated"]),
        (_deactivate_user, SENTENCES["deactivated"]),
        ("another org", SENTENCES["not_member"]),
        ("no owner", "Paused"),
    ],
    ids=["demoted", "deactivated", "user_deactivated", "other_org", "no_owner"],
)
def test_an_active_rule_the_engine_would_not_run_lists_as_paused(
    admin_client, org_a, profile_b, owner, unseen, sentence
):
    # Each change skips the signals that pause a rule.
    ravi = _member(org_a, "Ravi", role="ADMIN")
    _rule(org_a, name="Healthy", owner=owner, is_active=True)
    stale = _rule(org_a, name="Stale", owner=ravi, is_active=True, position=1)
    if unseen == "another org":
        AutomationRule.objects.filter(pk=stale.pk).update(owner=profile_b)
    elif unseen == "no owner":
        AutomationRule.objects.filter(pk=stale.pk).update(owner=None)
    else:
        unseen(ravi)

    listed = _listed(admin_client)

    assert (listed["Stale"]["status"], listed["Stale"]["status_text"]) == (
        "paused",
        sentence,
    )
    assert (listed["Healthy"]["status"], listed["Healthy"]["status_text"]) == (
        "on",
        "On",
    )


def test_listing_rules_the_engine_would_not_run_reads_no_row_per_rule(
    admin_client, org_a, owner
):
    def stale(n):
        person = _member(org_a, f"Former{n}", role="ADMIN")
        _rule(org_a, name=f"Stale {n}", owner=person, is_active=True, position=n)
        _demote(person)

    stale(0)
    admin_client.get(RULES)
    with CaptureQueriesContext(connection) as one_rule:
        listed = _listed(admin_client)
    assert listed["Stale 0"]["status"] == "paused"

    for n in range(1, 4):
        stale(n)
    with CaptureQueriesContext(connection) as four_rules:
        listed = _listed(admin_client)
    assert {row["status"] for row in listed.values()} == {"paused"}
    assert len(four_rules) == len(one_rule)


def test_switching_on_an_active_rule_the_engine_would_not_run_takes_it_over(
    admin_client, org_a, owner
):
    ravi = _member(org_a, "Ravi", role="ADMIN")
    rule = _rule(org_a, owner=ravi, is_active=True)
    _demote(ravi)
    assert _listed(admin_client)["Deal rule"]["status"] == "paused"

    refuses_all = RefusesAll()
    register_plan_hook(refuses_all)
    response = admin_client.patch(
        f"{RULES}{rule.id}/", {"is_active": True}, format="json"
    )
    assert (response.status_code, response.json()["code"]) == (403, "plan_limit")
    assert refuses_all.asked == ["Deal rule"]
    rule.refresh_from_db()
    assert rule.owner == ravi

    plan._HOOKS[:] = []
    before = timezone.now()
    response = admin_client.patch(
        f"{RULES}{rule.id}/", {"is_active": True}, format="json"
    )

    assert response.status_code == 200, response.content
    rule.refresh_from_db()
    assert (rule.owner, rule.is_active, rule.paused_reason) == (owner, True, "")
    assert rule.switched_on_at >= before
    listed = _listed(admin_client)["Deal rule"]
    assert (listed["status"], listed["status_text"]) == ("on", "On")


def test_switching_on_a_running_rule_changes_nothing(admin_client, org_a, owner):
    ravi = _member(org_a, "Ravi", role="ADMIN")
    rule = _rule(org_a, owner=ravi, is_active=True)
    switched_on_at = rule.switched_on_at
    refuses_all = RefusesAll()
    register_plan_hook(refuses_all)

    response = admin_client.patch(
        f"{RULES}{rule.id}/", {"is_active": True}, format="json"
    )

    assert response.status_code == 200, response.content
    rule.refresh_from_db()
    assert (rule.owner, rule.switched_on_at) == (ravi, switched_on_at)
    assert refuses_all.asked == []


def test_editing_an_active_rule_keeps_its_owner(org_a, owner):
    ravi = _member(org_a, "Ravi", role="ADMIN")
    rule = _rule(org_a, owner=owner, is_active=True)
    switched_on_at = rule.switched_on_at

    response = _client(ravi).patch(
        f"{RULES}{rule.id}/",
        {"name": "Renamed", "actions": [_set("probability", 50)], "is_active": True},
        format="json",
    )

    assert response.status_code == 200, response.content
    rule.refresh_from_db()
    assert (rule.name, rule.actions) == ("Renamed", [_set("probability", 50)])
    assert (rule.owner, rule.switched_on_at) == (owner, switched_on_at)


def test_a_plan_hook_refusal_answers_403_with_its_message(admin_client, org_a, owner):
    register_plan_hook(CapAtTwo())
    for n in range(2):
        response = admin_client.post(
            RULES, _body(name=f"Rule {n}", is_active=True), format="json"
        )
        assert response.status_code == 201, response.content

    refused = {"detail": CapAtTwo.message, "code": "plan_limit"}
    response = admin_client.post(
        RULES, _body(name="Third", is_active=True), format="json"
    )
    assert (response.status_code, response.json()) == (403, refused)
    # The plan answers before the rule is checked.
    response = admin_client.post(
        RULES, _body(name="Broken", actions=[], is_active=True), format="json"
    )
    assert (response.status_code, response.json()) == (403, refused)
    assert not AutomationRule.objects.filter(name__in=("Third", "Broken")).exists()

    off = _rule(org_a, name="Off rule", position=9)
    response = admin_client.patch(
        f"{RULES}{off.id}/", {"name": "Renamed", "is_active": True}, format="json"
    )
    assert (response.status_code, response.json()) == (403, refused)
    off.refresh_from_db()
    assert (off.name, off.is_active, off.owner) == ("Off rule", False, None)

    # Saving a rule off, or editing an active one, switches nothing on, so a
    # hook that refuses every switch-on is never asked.
    refuses_all = RefusesAll()
    plan._HOOKS[:] = []
    register_plan_hook(refuses_all)
    response = admin_client.post(RULES, _body(name="Saved off"), format="json")
    assert response.status_code == 201, response.content
    first = AutomationRule.objects.get(name="Rule 0")
    response = admin_client.patch(
        f"{RULES}{first.id}/", {"name": "Rule zero", "is_active": True}, format="json"
    )
    assert response.status_code == 200, response.content
    first.refresh_from_db()
    assert (first.name, first.is_active, first.owner) == ("Rule zero", True, owner)
    assert refuses_all.asked == []
    saved_off = AutomationRule.objects.get(name="Saved off")
    response = admin_client.patch(
        f"{RULES}{saved_off.id}/", {"is_active": True}, format="json"
    )
    assert response.status_code == 403, response.content
    assert refuses_all.asked == ["Saved off"]


def test_the_default_hook_allows_any_number(admin_client, org_a, owner):
    for n in range(12):
        response = admin_client.post(
            RULES, _body(name=f"Rule {n}", is_active=True), format="json"
        )
        assert response.status_code == 201, response.content
    active = AutomationRule.objects.filter(org=org_a, is_active=True, owner=owner)
    assert active.count() == 12
    assert {r["status"] for r in _listed(admin_client).values()} == {"on"}


def test_over_limit_status_comes_from_the_hook(admin_client, org_a, owner):
    hook = FirstOnly()
    register_plan_hook(hook)
    _rule(org_a, name="One", owner=owner, is_active=True, position=0)
    _rule(org_a, name="Two", owner=owner, is_active=True, position=1)
    _rule(org_a, name="Off", position=2)

    body = admin_client.get(RULES).json()

    assert body["summary"] == "1 of 2 active rules run"
    assert [(r["name"], r["status"], r["status_text"]) for r in body["results"]] == [
        ("One", "on", "On"),
        ("Two", "over_limit", OVER),
        ("Off", "off", "Off"),
    ]
    assert hook.asked == [["One", "Two"]]


def test_a_rule_whose_person_was_deactivated_needs_attention(
    admin_client, org_a, owner, deal
):
    asha = _member(org_a, "Asha")
    assign = {"type": "assign", "people": [str(asha.id)], "mode": "replace"}
    response = admin_client.post(
        RULES, _body(actions=[assign], is_active=True), format="json"
    )
    assert response.status_code == 201, response.content
    listed = _listed(admin_client)["Deal rule"]
    assert (listed["status"], listed["status_text"]) == ("on", "On")

    asha.is_active = False
    asha.save()

    listed = _listed(admin_client)["Deal rule"]
    assert listed["status"] == "needs_attention"
    assert listed["status_text"] == f"Needs attention: {NOT_A_MEMBER}"
    response = admin_client.patch(
        f"/api/opportunities/{deal.id}/", {"name": "Acme 2027"}, format="json"
    )
    assert response.status_code == 200, response.content
    [run] = AutomationRun.objects.filter(org=org_a)
    assert (run.status, run.reason) == (FAILED, f"actions[0].people: {NOT_A_MEMBER}")
    assert AutomationRule.objects.get().is_active
    listed = _listed(admin_client)["Deal rule"]
    assert (listed["runs_7d"], listed["failures_7d"]) == (1, 1)


# Trying a rule


def test_try_answers_steps_and_writes_nothing(admin_client, org_a, owner, deal):
    rule = _rule(org_a, actions=[_set("probability", 30), _task()])
    probability = deal.probability

    response = admin_client.post(
        f"{RULES}{rule.id}/try/", {"record_id": str(deal.id)}, format="json"
    )

    assert response.status_code == 200, response.content
    assert response.json() == {
        "steps": [
            {
                "action": 0,
                "type": "set_field",
                "status": "planned",
                "text": "Would set Probability to 30 on Acme renewal",
            },
            {
                "action": 1,
                "type": "create_task",
                "status": "planned",
                "text": "Would create the task 'Call Acme renewal' for Olga",
            },
        ]
    }
    deal.refresh_from_db()
    assert deal.probability == probability
    for model in (AutomationRun, Task, Notification):
        assert not model.objects.filter(org=org_a).exists(), model
    rule.refresh_from_db()
    assert (rule.owner, rule.is_active, rule.switched_on_at) == (None, False, None)


def test_try_on_another_orgs_record_is_404(admin_client, org_a, org_b, rule):
    with rls_org(org_b):
        theirs = _deal(org_b)
    lead = Lead.objects.create(org=org_a, title="A lead")
    url = f"{RULES}{rule.id}/try/"
    for body in (
        {"record_id": str(theirs.id)},
        {"record_id": str(lead.id)},
        {"record_id": "not-a-uuid"},
        {"record_id": 7},
        {"record_id": [str(theirs.id)]},
        {},
    ):
        response = admin_client.post(url, body, format="json")
        assert response.status_code == 404, body
    ours = _deal(org_a, "Ours")
    response = admin_client.post(url, {"record_id": str(ours.id)}, format="json")
    assert response.status_code == 200, response.content


# Runs


def test_runs_are_paginated_newest_first(admin_client, org_a, rule):
    upstream = _rule(org_a, name="Upstream", position=1)
    cause = _run(upstream)
    steps = [{"action": 0, "type": "set_field", "status": "done", "text": "Set"}]
    runs = AutomationRun.objects.bulk_create(
        AutomationRun(
            org=org_a,
            rule=rule,
            object_key="deal",
            record_id=uuid.uuid4(),
            record_name=f"Deal {n}",
            status=DONE,
            chain_id=uuid.uuid4(),
            depth=2,
            triggered_by=cause,
            steps=steps,
        )
        for n in range(105)
    )
    now = timezone.now()
    for n, run in enumerate(runs):
        AutomationRun.objects.filter(pk=run.pk).update(
            created_at=now - timedelta(minutes=n)
        )
    url = f"{RULES}{rule.id}/runs/"

    first = admin_client.get(url).json()

    assert set(first) == {"count", "results"}
    assert first["count"] == 105
    assert [r["record_name"] for r in first["results"]] == [
        f"Deal {n}" for n in range(20)
    ]
    newest = first["results"][0]
    assert parse_datetime(newest.pop("created_at")) == now
    assert newest == {
        "id": str(runs[0].id),
        "record_id": str(runs[0].record_id),
        "record_name": "Deal 0",
        "object_key": "deal",
        "status": "done",
        "reason": "",
        "steps": steps,
        "skipped_count": 0,
        "depth": 2,
        "triggered_by": {"id": str(cause.id), "rule_name": "Upstream"},
    }
    page = admin_client.get(url, {"limit": 5, "offset": 20}).json()
    assert [r["record_name"] for r in page["results"]] == [
        f"Deal {n}" for n in range(20, 25)
    ]
    assert len(admin_client.get(url, {"limit": 500}).json()["results"]) == 100
    assert len(admin_client.get(url, {"limit": "lots"}).json()["results"]) == 20
    upstream_runs = admin_client.get(f"{RULES}{upstream.id}/runs/").json()
    assert upstream_runs["count"] == 1
    assert upstream_runs["results"][0]["triggered_by"] is None


# Reordering


def test_reorder_refuses_foreign_ids(admin_client, org_a, org_b):
    one, two, three = (
        _rule(org_a, name=name, position=n)
        for n, name in enumerate(("One", "Two", "Three"))
    )
    with rls_org(org_b):
        theirs = _rule(org_b, name="Theirs", position=7)
    url = f"{RULES}reorder/"

    def positions():
        rules = AutomationRule.objects.filter(org=org_a)
        return dict(rules.values_list("name", "position"))

    for ids in (
        [str(three.id), str(theirs.id)],
        [str(one.id), "not-a-uuid"],
        [str(one.id), str(one.id)],
        str(one.id),
        None,
    ):
        response = admin_client.post(url, {"ids": ids}, format="json")
        assert response.status_code == 400, ids
        assert list(response.json()["errors"]) == ["ids"], ids
    assert positions() == {"One": 0, "Two": 1, "Three": 2}
    with rls_org(org_b):
        theirs.refresh_from_db()
    assert theirs.position == 7

    response = admin_client.post(
        url, {"ids": [str(three.id), str(one.id)]}, format="json"
    )

    assert response.status_code == 200, response.content
    # A rule the list leaves out keeps its place after the ones it names.
    assert response.json() == {"ids": [str(three.id), str(one.id), str(two.id)]}
    assert positions() == {"Three": 0, "One": 1, "Two": 2}
    assert list(_listed(admin_client)) == ["Three", "One", "Two"]


# The catalogue


def test_the_catalogue_offers_only_json_endpoints_and_active_people(
    admin_client, org_a, org_b, owner
):
    asha = _member(org_a, "Asha")
    gone = _member(org_a, "Gone")
    gone.is_active = False
    gone.save()
    left = _member(org_a, "Left")
    User.objects.filter(pk=left.user_id).update(is_active=False)
    with rls_org(org_b):
        _member(org_b, "Bo")
        WebhookEndpoint.objects.create(
            org=org_b,
            url="https://b.example.com/in",
            events=["deal.updated"],
            description="Theirs",
        )
    hook = {"url": "https://hooks.example.com/in", "events": ["deal.updated"]}
    zapier = WebhookEndpoint.objects.create(org=org_a, description="Zapier", **hook)
    unnamed = WebhookEndpoint.objects.create(org=org_a, **hook)
    WebhookEndpoint.objects.create(org=org_a, description="Slack", format=SLACK, **hook)
    WebhookEndpoint.objects.create(
        org=org_a, description="Off", is_active=False, **hook
    )

    response = admin_client.get(f"{BASE}catalogue/")

    assert response.status_code == 200
    body = response.json()
    assert body["people"] == [
        {"id": str(asha.id), "name": "Asha"},
        {"id": str(owner.id), "name": "Olga"},
    ]
    assert body["endpoints"] == [
        {"id": str(zapier.id), "description": "Zapier"},
        {"id": str(unnamed.id), "description": "hooks.example.com"},
    ]
    assert body["actions"] == [
        "set_field",
        "assign",
        "create_task",
        "notify",
        "webhook",
    ]
    assert body["limits"] == {"conditions": 20, "actions": 10}
    assert body["operators"]["boolean"] == ["true", "false"]
    assert body["update_only_operators"] == ["was", "was_not"]


def test_the_catalogue_describes_each_object_rules_can_reach(admin_client, org_a):
    DealPipeline.default_for(org_a)
    register_link_hook(DealLinks())

    body = admin_client.get(f"{BASE}catalogue/").json()

    objects = {o["key"]: o for o in body["objects"]}
    assert list(objects) == ["lead", "contact", "account", "deal", "ticket", "task"]
    deal = objects["deal"]
    assert (deal["label"], deal["label_plural"]) == ("Deal", "Deals")
    assert deal["parent"] == {"key": "account", "label": "Account"}
    assert objects["ticket"]["parent"] == {"key": "account", "label": "Account"}
    assert objects["task"]["parent"] is None
    assert objects["lead"]["parent"] is None
    # A link to an object rules cannot reach is not offered.
    assert deal["links"] == [
        {
            "id": "in:visits.deals",
            "label": "Visits linked through Deals",
            "object_key": "lead",
        }
    ]
    assert objects["lead"]["links"] == []

    fields = {f["key"]: f for f in deal["fields"]}
    assert fields["stage_kind"] == {
        "key": "stage_kind",
        "label": "Outcome",
        "type": "choice",
        "choices": [
            {
                "value": "open",
                "label": "Open (any pipeline)",
                "group": "",
                "settable": True,
            },
            {
                "value": "won",
                "label": "Won (any pipeline)",
                "group": "",
                "settable": True,
            },
            {
                "value": "lost",
                "label": "Lost (any pipeline)",
                "group": "",
                "settable": True,
            },
        ],
        "settable": False,
    }
    stages = fields["stage"]["choices"]
    assert stages and {c["group"] for c in stages} == {
        DealPipeline.default_for(org_a).name
    }
    assert fields["assigned_to"]["type"] == "people"
    lead_status = {f["key"]: f for f in objects["lead"]["fields"]}["status"]
    converted = next(c for c in lead_status["choices"] if c["value"] == "converted")
    assert converted["settable"] is False
