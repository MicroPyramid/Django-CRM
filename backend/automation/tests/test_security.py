"""Rows of the design's security table that no other test file covers.

Each test is named after the abuse it shuts. The table's other rows are
covered where their code lives (test_api, test_validation, test_adapters,
test_actions, test_engine, test_ownership, test_capture, test_acceptance).
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.db import DatabaseError, connection, transaction
from django.utils import timezone

from automation.limits import RUNS_PER_HOUR
from automation.models import (
    DONE,
    FAILED,
    SKIPPED,
    AutomationRotation,
    AutomationRule,
    AutomationRun,
)
from cases.models import Case
from common.models import Activity, Notification, Profile, User
from conftest import rls_org
from leads.models import Lead
from opportunity.models import DealPipeline, Opportunity
from tasks.models import Task
from webforms.models import WebForm, WebFormField

RULES = "/api/automation/rules/"
EMAIL = "automation.actions.send_member_email.delay"
CREATED = {"event": "created", "field": None, "to": None}
NAME_CHANGES = {"event": "updated", "field": "name", "to": None}
UNKNOWN_FIELD = "This field is not available."
SERVER_OWNED = (
    "org",
    "id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "is_active",
    "is_sample",
    "token",
    "api_key",
)
# A field each object's edit form writes.
CATALOGUE_FIELD = {
    "lead": "title",
    "contact": "first_name",
    "account": "name",
    "deal": "name",
    "ticket": "name",
    "task": "title",
}
NOW = datetime(2026, 10, 22, 14, 30, tzinfo=UTC)


@pytest.fixture(autouse=True)
def fresh_cache():
    cache.clear()


@pytest.fixture
def owner(admin_profile):
    admin_profile.user.name = "Olga"
    admin_profile.user.save(update_fields=["name"])
    return admin_profile


@pytest.fixture
def commit(django_capture_on_commit_callbacks):
    return lambda: django_capture_on_commit_callbacks(execute=True)


def _member(org, name, *, role="USER"):
    user = User.objects.create_user(
        email=f"{name.lower()}@example.com", password="testpass123", name=name
    )
    return Profile.objects.create(user=user, org=org, role=role, is_active=True)


def _body(object_key="deal", trigger=NAME_CHANGES, actions=(), name="Rule"):
    return {
        "name": name,
        "object_key": object_key,
        "trigger": trigger,
        "match": "all",
        "conditions": [],
        "actions": list(actions),
        "is_active": True,
    }


def _build(client, **fields):
    response = client.post(RULES, _body(**fields), format="json")
    assert response.status_code == 201, response.content
    return AutomationRule.objects.get(pk=response.json()["id"])


def _rule(org, owner, actions, *, name="Rule", position=0):
    return AutomationRule.objects.create(
        org=org,
        name=name,
        object_key="deal",
        trigger=dict(NAME_CHANGES),
        actions=list(actions),
        owner=owner,
        is_active=True,
        position=position,
        switched_on_at=timezone.now(),
    )


def _deal(org, name="Acme renewal", **values):
    return Opportunity.objects.create(
        org=org,
        name=name,
        pipeline=DealPipeline.default_for(org),
        stage="QUALIFICATION",
        **values,
    )


def _set(field, value):
    return {"type": "set_field", "target": "record", "field": field, "value": value}


def _task(assign_to="owner", person=None):
    return {
        "type": "create_task",
        "title": "Call {name}",
        "due_in_days": None,
        "priority": "High",
        "assign_to": assign_to,
        "person": person,
    }


def _notify(to=(), people=()):
    return {
        "type": "notify",
        "to": list(to),
        "people": list(people),
        "message": "{name} moved",
    }


def _rename(client, deal, name="Acme 2027"):
    response = client.patch(
        f"/api/opportunities/{deal.pk}/", {"name": name}, format="json"
    )
    assert response.status_code == 200, response.content


def _rls_binds():
    """Whether this connection's role is subject to row-level security."""
    if connection.vendor != "postgresql":
        return False
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user"
        )
        return not cursor.fetchone()[0]


def _need_rls():
    if connection.vendor != "postgresql":
        pytest.skip("Row-level security is a PostgreSQL feature")
    if not _rls_binds():
        pytest.skip("Needs a role row-level security binds, as in CI")


# A rule writes `org`, `created_by`, `is_active` or a token


@pytest.mark.parametrize("object_key", sorted(CATALOGUE_FIELD))
def test_a_rule_cannot_write_server_owned_fields_at_save(
    admin_client, org_a, object_key
):
    refused = [_set(field, "x") for field in SERVER_OWNED]
    response = admin_client.post(
        RULES, _body(object_key, CREATED, refused), format="json"
    )
    assert response.status_code == 400, response.content
    errors = response.json()["errors"]
    assert errors == {
        f"actions[{index}].field": [UNKNOWN_FIELD] for index in range(len(refused))
    }
    assert not AutomationRule.objects.filter(org=org_a).exists()

    accepted = [_set(CATALOGUE_FIELD[object_key], "Set by a rule")]
    response = admin_client.post(
        RULES, _body(object_key, CREATED, accepted), format="json"
    )
    assert response.status_code == 201, response.content


def test_a_rule_cannot_write_server_owned_fields_at_run(
    admin_client, org_a, org_b, owner, admin_user
):
    deal = _deal(org_a, probability=5)
    rule = _build(admin_client, actions=[_set("probability", 30)])
    for forced in (
        _set("org", str(org_b.pk)),
        _set("created_by", str(uuid.uuid4())),
        _set("is_active", False),
    ):
        AutomationRule.objects.filter(pk=rule.pk).update(
            actions=[_set("probability", 30), forced]
        )
        _rename(admin_client, deal, f"Acme {forced['field']}")

    runs = AutomationRun.objects.filter(org=org_a, rule=rule)
    assert [(run.status, run.steps) for run in runs] == [(FAILED, [])] * 3
    assert {run.reason for run in runs} == {f"actions[1].field: {UNKNOWN_FIELD}"}
    deal.refresh_from_db()
    assert (deal.org_id, deal.created_by_id, deal.is_active) == (org_a.pk, None, True)
    assert deal.probability == 5


# Mail to outsiders through rules


def test_mail_to_outsiders_is_refused_and_inactive_members_are_skipped(
    admin_client, org_a, owner, commit
):
    asha, gone, locked = (_member(org_a, n) for n in ("Asha", "Gone", "Locked"))
    for action, path in (
        (_notify(to=["someone@example.com"]), "actions[0].to"),
        (_notify(people=["someone@example.com"]), "actions[0].people"),
        (_notify(people=[str(asha.pk), "someone@example.com"]), "actions[0].people"),
    ):
        response = admin_client.post(RULES, _body(actions=[action]), format="json")
        assert response.status_code == 400, response.content
        assert list(response.json()["errors"]) == [path]

    deal = _deal(org_a)
    deal.assigned_to.add(asha, gone, locked)
    rule = _build(admin_client, actions=[_notify(to=["record_assignees"])])
    Profile.objects.filter(pk=gone.pk).update(is_active=False)
    User.objects.filter(pk=locked.user_id).update(is_active=False)

    with patch(EMAIL) as email, commit():
        _rename(admin_client, deal)

    run = AutomationRun.objects.get(org=org_a, rule=rule)
    assert (run.status, run.steps[0]["text"]) == (DONE, "Notified Asha")
    notices = Notification.objects.filter(org=org_a, verb="automation.message")
    assert [notice.recipient for notice in notices] == [asha]
    email.assert_called_once()
    assert email.call_args.args[0] == [str(asha.pk)]


# A rule's change is credited to the person who saved


def test_a_rules_task_on_a_web_form_lead_is_credited_to_its_owner(
    unauthenticated_client, admin_client, org_a, owner, admin_user
):
    form = WebForm.objects.create(
        name="Contact us", org=org_a, is_published=True, lead_source="other"
    )
    WebFormField.objects.create(
        form=form,
        org=org_a,
        order=0,
        source=WebFormField.SOURCE_LEAD,
        lead_field="email",
        label="Email",
        is_required=True,
    )
    _build(
        admin_client,
        name="Call web leads",
        object_key="lead",
        trigger=CREATED,
        actions=[_task()],
    )

    response = unauthenticated_client.post(
        f"/api/public/forms/{org_a.pk}/{form.pk}/submit/",
        {"email": "pat@example.com"},
        format="json",
    )

    assert response.status_code == 200, response.content
    lead = Lead.objects.get(org=org_a, email="pat@example.com")
    task = Task.objects.get(org=org_a)
    assert (task.lead, task.created_by) == (lead, admin_user)
    assert list(task.assigned_to.all()) == [owner]
    row = Activity.objects.get(org=org_a, entity_id=task.pk, action="CREATE")
    assert (row.user, row.metadata) == (owner, {"automation": "Call web leads"})


# A bulk ticket edit floods rules


def test_bulk_closing_200_tickets_runs_no_rules(admin_client, org_a, owner):
    _build(
        admin_client,
        name="Follow up closed tickets",
        object_key="ticket",
        trigger={"event": "updated", "field": "status", "to": "Closed"},
        actions=[_task()],
    )
    Case.objects.bulk_create(
        Case(org=org_a, name=f"Ticket {n}", status="New", priority="Normal")
        for n in range(201)
    )
    *batch, single = Case.objects.filter(org=org_a)

    response = admin_client.post(
        "/api/cases/bulk/update/",
        {"ids": [str(t.pk) for t in batch], "fields": {"status": "Closed"}},
        format="json",
    )

    assert response.status_code == 200, response.content
    assert response.json()["updated"] == 200
    assert Case.objects.filter(org=org_a, status="Closed").count() == 200
    assert not AutomationRun.objects.filter(org=org_a).exists()
    assert not Task.objects.filter(org=org_a).exists()

    # The rule is live: closing one ticket on its own runs it.
    response = admin_client.patch(
        f"/api/cases/{single.pk}/", {"status": "Closed"}, format="json"
    )
    assert response.status_code == 200, response.content
    assert [run.status for run in AutomationRun.objects.filter(org=org_a)] == [DONE]
    assert Task.objects.filter(org=org_a).count() == 1


# A flood grows the run table


def test_a_flood_leaves_the_hours_runs_and_one_counted_row_per_rule(
    org_a, owner, commit
):
    first = _rule(org_a, owner, [_set("probability", 30)], name="First")
    second = _rule(org_a, owner, [_set("amount", 500)], name="Second", position=1)
    deals = [_deal(org_a, name=f"Deal {n}", probability=5) for n in range(5)]
    renames = 0

    with patch("django.utils.timezone.now", return_value=NOW):
        AutomationRun.objects.bulk_create(
            AutomationRun(
                org=org_a,
                rule=first,
                object_key="deal",
                record_id=deals[0].pk,
                record_name=deals[0].name,
                status=DONE,
                chain_id=uuid.uuid4(),
            )
            for _ in range(RUNS_PER_HOUR)
        )
        for round_ in range(3):
            for deal in deals:
                with commit():
                    deal.name = f"Deal {deal.pk} {round_}"
                    deal.save()
                renames += 1

    runs = AutomationRun.objects.filter(org=org_a)
    assert runs.count() == RUNS_PER_HOUR + 2
    assert runs.exclude(status=SKIPPED).count() == RUNS_PER_HOUR
    counted = runs.filter(status=SKIPPED).values_list("rule", "skipped_count")
    assert sorted(counted) == sorted([(first.pk, renames), (second.pk, renames)])
    for deal in deals:
        deal.refresh_from_db()
        assert (deal.probability, deal.amount) == (5, None)


# A rule names another org's person, endpoint or record


@pytest.mark.postgres_only
def test_a_run_never_touches_another_org(
    admin_client, org_a, org_b, owner, profile_b, commit
):
    _need_rls()
    deal = _deal(org_a, probability=5)
    with rls_org(org_b):
        theirs = _deal(org_b, name="Their deal", probability=5)
    rule = _build(admin_client, actions=[_set("probability", 30)])
    them = str(profile_b.pk)
    AutomationRule.objects.filter(pk=rule.pk).update(
        actions=[
            _set("probability", 30),
            {"type": "assign", "people": [them], "mode": "replace"},
            _set("assigned_to", [them]),
            _task(assign_to="person", person=them),
            _notify(people=[them]),
        ]
    )

    with patch(EMAIL) as email, commit():
        _rename(admin_client, deal)

    run = AutomationRun.objects.get(org=org_a, rule=rule)
    assert (run.status, run.steps) == (FAILED, [])
    assert run.reason.startswith("actions[1].people: ")
    deal.refresh_from_db()
    assert deal.probability == 5
    assert not deal.assigned_to.exists()
    assert not Task.objects.filter(org=org_a).exists()
    email.assert_not_called()
    with rls_org(org_b):
        # Unfiltered on purpose: under org B's context RLS shows only its rows.
        for model in (Task, Notification, AutomationRun, Activity):
            assert not model.objects.exists(), model
        theirs.refresh_from_db()
        assert theirs.probability == 5
        assert not theirs.assigned_to.exists()


def _seed(org, owner):
    rule = AutomationRule.objects.create(
        org=org,
        name=f"Rule of {org.name}",
        object_key="deal",
        trigger=dict(NAME_CHANGES),
        actions=[_set("probability", 30)],
        owner=owner,
    )
    run = AutomationRun.objects.create(
        org=org,
        rule=rule,
        object_key="deal",
        record_id=uuid.uuid4(),
        record_name="A deal",
        status=DONE,
        chain_id=uuid.uuid4(),
    )
    rotation = AutomationRotation.objects.create(org=org, rule=rule, action_index=0)
    return {AutomationRule: rule, AutomationRun: run, AutomationRotation: rotation}


@pytest.mark.postgres_only
def test_rule_tables_are_isolated(org_a, org_b, owner, profile_b):
    _need_rls()
    with rls_org(org_a):
        mine = _seed(org_a, owner)
    with rls_org(org_b):
        theirs = _seed(org_b, profile_b)

    for org, own, other, other_org in (
        (org_a, mine, theirs, org_b),
        (org_b, theirs, mine, org_a),
    ):
        with rls_org(org):
            for model, row in own.items():
                assert list(model.objects.values_list("pk", flat=True)) == [row.pk]
                hidden = model.objects.filter(pk=other[model].pk)
                assert not hidden.exists(), model
                assert hidden.update(updated_at=timezone.now()) == 0, model
            with pytest.raises(DatabaseError), transaction.atomic():
                AutomationRule.objects.create(
                    org=other_org, name="Planted", object_key="deal"
                )
            with pytest.raises(DatabaseError), transaction.atomic():
                AutomationRotation.objects.create(
                    org=other_org, rule=other[AutomationRule], action_index=1
                )
    with rls_org(org_b):
        assert AutomationRule.objects.get().name == "Rule of Test Organization B"
