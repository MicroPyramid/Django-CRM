"""The rule engine: which rules a change sets off, how they run, as whom, how often."""

import logging
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from celery.schedules import crontab
from crum import get_current_user
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from automation import plan
from automation.capture import Change
from automation.engine import UNDONE, process, try_rule
from automation.limits import RUN_RETENTION_DAYS, RUNS_PER_HOUR
from automation.models import (
    DONE,
    FAILED,
    SKIPPED,
    AutomationRotation,
    AutomationRule,
    AutomationRun,
)
from automation.plan import Runnable, register_plan_hook
from automation.tasks import prune_org_runs, prune_runs, send_member_email
from cases.models import Case
from common.models import Activity, Notification, Profile, User
from common.tasks import set_rls_context as set_session_org
from conftest import restore_rls_context, rls_org
from crm.celery import app
from opportunity.models import DealPipeline, DealStage, Opportunity
from tasks.models import Task
from webhooks.models import WebhookDelivery, WebhookEndpoint

EMAIL = "automation.actions.send_member_email.delay"
DELIVER = "webhooks.emit.deliver_webhook.delay"
NAME_CHANGES = {"event": "updated", "field": "name", "to": None}
CREATED = {"event": "created", "field": None, "to": None}
NOT_CLOSED = "A deal cannot be closed without the date it closed on."
TO_WON = {"event": "updated", "field": "stage_kind", "to": "won"}
NOW = datetime(2026, 10, 22, 14, 30, tzinfo=UTC)
WINDOW = NOW.replace(minute=0)
GENERIC = "Something went wrong in this step"


@pytest.fixture(autouse=True)
def fresh_state():
    saved = list(plan._HOOKS)
    cache.clear()
    yield
    plan._HOOKS[:] = saved


@pytest.fixture
def owner(admin_profile):
    admin_profile.user.name = "Olga"
    admin_profile.user.save(update_fields=["name"])
    return admin_profile


@pytest.fixture
def commit(django_capture_on_commit_callbacks):
    """Run what waits for a commit, as the block's transaction committing would."""
    return lambda: django_capture_on_commit_callbacks(execute=True)


def _member(org, name, *, role="USER"):
    user = User.objects.create_user(
        email=f"{name.lower()}@example.com", password="testpass123", name=name
    )
    return Profile.objects.create(user=user, org=org, role=role, is_active=True)


def _rule(
    org,
    owner,
    actions,
    *,
    name="Deal rule",
    object_key="deal",
    trigger=NAME_CHANGES,
    conditions=(),
    position=0,
):
    return AutomationRule.objects.create(
        org=org,
        name=name,
        object_key=object_key,
        trigger=dict(trigger),
        conditions=list(conditions),
        actions=list(actions),
        owner=owner,
        is_active=True,
        position=position,
        switched_on_at=timezone.now(),
    )


def _deal(org, name="Acme renewal", **values):
    pipeline = DealPipeline.default_for(org)
    return Opportunity.objects.create(
        org=org, name=name, pipeline=pipeline, stage="QUALIFICATION", **values
    )


def _won(deal):
    return str(DealStage.objects.get(pipeline=deal.pipeline, code="CLOSED_WON").pk)


def _rename(record, name):
    record.name = name
    record.save()


def _set(field, value, target="record"):
    return {"type": "set_field", "target": target, "field": field, "value": value}


def _task(priority="High", assign_to="owner"):
    return {
        "type": "create_task",
        "title": "Call {name}",
        "due_in_days": None,
        "priority": priority,
        "assign_to": assign_to,
        "person": None,
    }


def _is(field, value):
    return {"field": field, "op": "eq", "value": value}


def _runs(org):
    return AutomationRun.objects.filter(org=org)


def _step(action, kind, status, text):
    return {"action": action, "type": kind, "status": status, "text": text}


def _past_run(rule, record, days):
    run = AutomationRun.objects.create(
        org=rule.org,
        rule=rule,
        object_key=rule.object_key,
        record_id=record.pk,
        record_name=str(record),
        status=DONE,
        chain_id=uuid.uuid4(),
    )
    AutomationRun.objects.filter(pk=run.pk).update(
        created_at=timezone.now() - timedelta(days=days)
    )
    return run


def _is_write(sql):
    statement = sql.lstrip().upper()
    return statement.startswith(("INSERT", "UPDATE", "DELETE")) or "FOR UPDATE" in (
        statement
    )


def _at_now():
    return patch("django.utils.timezone.now", return_value=NOW)


def _fill_the_hour(rule, record):
    """`RUNS_PER_HOUR` runs of `rule` in its org; call it inside `_at_now()`."""
    AutomationRun.objects.bulk_create(
        AutomationRun(
            org=rule.org,
            rule=rule,
            object_key=rule.object_key,
            record_id=record.pk,
            record_name=str(record),
            status=DONE,
            chain_id=uuid.uuid4(),
        )
        for _ in range(RUNS_PER_HOUR)
    )


class NoRulesRun:
    def __init__(self):
        self.asked = None

    def may_switch_on(self, org, rule):
        return None

    def runnable(self, org, rules):
        self.asked = sorted(rule.name for rule in rules)
        return Runnable(frozenset(), {}, None)


# Running


def test_a_matching_rule_runs_and_records_its_steps(org_a, owner, commit):
    deal = _deal(org_a)
    rule = _rule(
        org_a,
        owner,
        [_set("probability", 40), _task()],
        name="Renewals",
        conditions=[{"field": "name", "op": "contains", "value": "renewal"}],
    )
    _rule(
        org_a,
        owner,
        [_set("probability", 90)],
        name="Never",
        position=1,
        conditions=[{"field": "name", "op": "contains", "value": "nothing like it"}],
    )

    with commit():
        _rename(deal, "Acme renewal 2027")

    [run] = _runs(org_a)
    assert (run.rule, run.status, run.reason) == (rule, DONE, "")
    assert (run.object_key, run.record_id, run.record_name) == (
        "deal",
        deal.pk,
        "Acme renewal 2027",
    )
    assert (run.depth, run.triggered_by, run.skipped_count) == (1, None, 0)
    assert isinstance(run.chain_id, uuid.UUID)
    assert run.steps == [
        _step(0, "set_field", DONE, "Set Probability to 40 on Acme renewal 2027"),
        _step(
            1,
            "create_task",
            DONE,
            "Created the task 'Call Acme renewal 2027' for Olga",
        ),
    ]
    deal.refresh_from_db()
    assert deal.probability == 40
    task = Task.objects.get(org=org_a)
    assert (task.title, task.opportunity) == ("Call Acme renewal 2027", deal)
    assert list(task.assigned_to.all()) == [owner]


def test_rules_run_in_list_order_and_all_matching_rules_run(org_a, owner, commit):
    deal = _deal(org_a)
    second = _rule(org_a, owner, [_set("probability", 20)], name="Two", position=1)
    first = _rule(
        org_a,
        owner,
        [_set("probability", 10), _set("amount", 500)],
        name="One",
        position=0,
    )

    with commit():
        _rename(deal, "Acme 2027")

    deal.refresh_from_db()
    assert (deal.probability, deal.amount) == (20, Decimal("500"))
    runs = _runs(org_a).order_by("created_at")
    assert [(run.rule, run.status) for run in runs] == [(first, DONE), (second, DONE)]


def test_a_failing_step_rolls_back_that_rule_only(org_a, owner, commit):
    deal = _deal(org_a, probability=5, closed_on=date(2026, 10, 1))
    breaks = _rule(
        org_a,
        owner,
        [
            _set("probability", 10),
            _set("city", "Pune", target="parent"),
            _set("stage", _won(deal)),
        ],
        name="Breaks",
        position=0,
    )
    works = _rule(org_a, owner, [_set("amount", 500)], name="Works", position=1)

    with commit():
        _rename(deal, "Acme 2027")

    deal.refresh_from_db()
    assert (deal.probability, deal.stage, deal.amount) == (
        5,
        "QUALIFICATION",
        Decimal("500"),
    )
    failed = _runs(org_a).get(rule=breaks)
    worth = "A won deal has to record what it was worth."
    assert (failed.status, failed.reason) == (FAILED, worth)
    # "done" always means the change stands; a skipped step stays skipped.
    assert failed.steps == [
        _step(0, "set_field", UNDONE, "Set Probability to 10 on Acme 2027"),
        _step(1, "set_field", SKIPPED, "This deal has no account"),
        _step(2, "set_field", FAILED, worth),
    ]
    assert _runs(org_a).get(rule=works).status == DONE


def test_a_rule_acts_once_per_record_per_chain(org_a, owner, commit):
    deal = _deal(org_a)
    rule = _rule(org_a, owner, [_set("name", "Renamed by a rule")])

    with commit():
        _rename(deal, "Acme 2027")

    deal.refresh_from_db()
    assert deal.name == "Renamed by a rule"
    assert [(run.rule, run.depth) for run in _runs(org_a)] == [(rule, 1)]


def test_a_rule_never_runs_on_a_record_its_own_run_created(org_a, owner, commit):
    rule = _rule(
        org_a, owner, [_task()], name="Follow up", object_key="task", trigger=CREATED
    )

    with commit():
        first = Task.objects.create(
            org=org_a, title="Start", status="New", priority="High"
        )

    # The skipped run on the follow-up leaves no row, as a repeat on one record does.
    [run] = _runs(org_a)
    assert (run.rule, run.record_id, run.depth, run.status) == (rule, first.pk, 1, DONE)
    titles = Task.objects.filter(org=org_a).values_list("title", flat=True)
    assert sorted(titles) == ["Call Start", "Start"]


def test_a_rule_that_moves_the_record_back_stops_the_next_rules_trigger(
    org_a, owner, commit
):
    deal = _deal(org_a, amount=900, closed_on=date(2026, 10, 1), probability=5)
    reopen = str(DealStage.objects.get(pipeline=deal.pipeline, code="QUALIFICATION").pk)
    reopens = _rule(
        org_a, owner, [_set("stage", reopen)], name="Reopen", trigger=TO_WON
    )
    _rule(
        org_a,
        owner,
        [_set("probability", 77)],
        name="Celebrate",
        trigger=TO_WON,
        position=1,
    )

    with commit():
        deal.stage = "CLOSED_WON"
        deal.save()

    assert [run.rule for run in _runs(org_a)] == [reopens]
    deal.refresh_from_db()
    assert deal.stage == "QUALIFICATION"
    assert deal.probability != 77


def test_two_rules_ping_ponging_stop_at_depth_three(org_a, owner, commit):
    to_low = _rule(
        org_a,
        owner,
        [_task(priority="Low")],
        name="High makes Low",
        object_key="task",
        trigger=CREATED,
        conditions=[_is("priority", "High")],
    )
    to_high = _rule(
        org_a,
        owner,
        [_task(priority="High")],
        name="Low makes High",
        object_key="task",
        trigger=CREATED,
        conditions=[_is("priority", "Low")],
        position=1,
    )

    with commit():
        Task.objects.create(org=org_a, title="Start", status="New", priority="High")

    runs = list(_runs(org_a).order_by("depth"))
    assert [(run.rule, run.depth, run.status) for run in runs] == [
        (to_low, 1, DONE),
        (to_high, 2, DONE),
        (to_low, 3, DONE),
    ]
    assert [run.triggered_by for run in runs] == [None, runs[0], runs[1]]
    assert len({run.chain_id for run in runs}) == 1
    # The third run's task is made, but nothing is run on it.
    assert Task.objects.filter(org=org_a).count() == 4


def test_a_rule_runs_inside_a_request_before_the_response(admin_client, org_a, owner):
    deal = _deal(org_a)
    _rule(org_a, owner, [_set("probability", 30)])

    response = admin_client.patch(
        f"/api/opportunities/{deal.pk}/", {"name": "Acme 2027"}, format="json"
    )
    assert response.status_code == 200, response.content
    assert _runs(org_a).get().status == DONE

    response = admin_client.get(f"/api/opportunities/{deal.pk}/")
    assert response.status_code == 200, response.content
    assert response.json()["opportunity_obj"]["probability"] == 30


# Who a rule acts as


def test_a_rules_changes_are_credited_to_its_owner(
    org_a, owner, admin_user, user_client, user_profile
):
    deal = _deal(org_a)
    deal.assigned_to.add(user_profile)
    _rule(org_a, owner, [_set("probability", 30), _task()], name="Kick-off")

    response = user_client.patch(
        f"/api/opportunities/{deal.pk}/", {"name": "Acme 2027"}, format="json"
    )

    assert response.status_code == 200, response.content
    task = Task.objects.get(org=org_a)
    assert task.created_by == admin_user
    deal.refresh_from_db()
    assert (deal.probability, deal.updated_by) == (30, admin_user)

    rows = list(
        Activity.objects.filter(
            org=org_a, entity_type="Opportunity", entity_id=deal.pk, action="UPDATE"
        )
    )
    assert {row.user_id for row in rows} == {owner.pk, user_profile.pk}
    for row in rows:
        by_rule = row.user_id == owner.pk
        assert row.metadata == ({"automation": "Kick-off"} if by_rule else {})
    created = Activity.objects.get(org=org_a, entity_id=task.pk, action="CREATE")
    assert (created.user, created.metadata) == (owner, {"automation": "Kick-off"})


def test_outside_a_request_a_rules_writes_are_credited_to_its_owner(
    org_a, owner, admin_user, commit
):
    deal = _deal(org_a)
    _rule(org_a, owner, [_set("probability", 30)], name="Kick-off")

    with commit():
        _rename(deal, "Acme 2027")

    deal.refresh_from_db()
    assert (deal.probability, deal.updated_by) == (30, admin_user)
    rows = Activity.objects.filter(org=org_a, entity_id=deal.pk)
    assert rows.exists()
    for row in rows:
        assert (row.user, row.action) == (owner, "UPDATE")
        assert row.metadata == {"automation": "Kick-off"}
    assert get_current_user() is None


def test_a_rule_changing_a_ticket_writes_its_activity_with_the_owner_and_the_note(
    org_a, owner, commit
):
    ticket = Case.objects.create(
        org=org_a, name="Login bug", status="New", priority="Low"
    )
    _rule(
        org_a, owner, [_set("priority", "Urgent")], name="Escalate", object_key="ticket"
    )

    with commit():
        _rename(ticket, "Login bug, again")

    ticket.refresh_from_db()
    assert ticket.priority == "Urgent"
    row = Activity.objects.get(
        org=org_a, entity_id=ticket.pk, action="PRIORITY_CHANGED"
    )
    assert row.user == owner
    assert row.metadata == {
        "before": "Low",
        "after": "Urgent",
        "automation": "Escalate",
    }
    # The save that set the rule off was nobody's and is written as before; the
    # rule's own UPDATE row (its new priority's SLA targets) is the owner's.
    updates = Activity.objects.filter(org=org_a, entity_id=ticket.pk, action="UPDATE")
    rename = updates.get(user=None)
    assert rename.metadata == {
        "changes": {"name": {"before": "Login bug", "after": "Login bug, again"}}
    }
    by_rule = updates.get(user=owner)
    assert by_rule.metadata["automation"] == "Escalate"
    assert set(by_rule.metadata["changes"]) == {
        "sla_first_response_hours",
        "sla_resolution_hours",
    }


@pytest.mark.parametrize(
    "how", ["no owner", "profile off", "user off", "not an admin", "another org"]
)
def test_a_rule_runs_only_as_an_active_admin_of_its_org(
    how, org_a, org_b, owner, commit
):
    deal = _deal(org_a, probability=5)
    rule = _rule(org_a, owner, [_set("probability", 30)])
    if how == "no owner":
        rule.owner = None
        rule.save()
    elif how == "profile off":
        Profile.objects.filter(pk=owner.pk).update(is_active=False)
    elif how == "user off":
        User.objects.filter(pk=owner.user_id).update(is_active=False)
    elif how == "not an admin":
        Profile.objects.filter(pk=owner.pk).update(role="USER")
    else:
        rule.owner = _member(org_b, "Bo", role="ADMIN")
        rule.save()

    with commit():
        _rename(deal, "Acme 2027")

    assert not _runs(org_a).exists()
    deal.refresh_from_db()
    assert deal.probability == 5


# Failures and skips


def test_a_rule_that_no_longer_validates_fails_before_writing(org_a, owner, commit):
    gone = _member(org_a, "Gone")
    deal = _deal(org_a, probability=5)
    rule = _rule(
        org_a,
        owner,
        [
            _set("probability", 30),
            {"type": "assign", "people": [str(gone.pk)], "mode": "replace"},
        ],
    )
    Profile.objects.filter(pk=gone.pk).update(is_active=False)

    with commit():
        _rename(deal, "Acme 2027")

    [run] = _runs(org_a)
    assert (run.rule, run.status, run.steps) == (rule, FAILED, [])
    assert run.reason == (
        "actions[1].people: Each person must be an active member of this org."
    )
    deal.refresh_from_db()
    assert deal.probability == 5


def test_a_skipped_step_is_recorded_and_the_next_step_runs(org_a, owner, commit):
    deal = _deal(org_a)
    _rule(
        org_a,
        owner,
        [
            _set("city", "Pune", target="parent"),
            _set("probability", 30),
            {
                "type": "notify",
                "to": ["record_assignees"],
                "people": [],
                "message": "{name} moved",
            },
            _set("amount", 500),
        ],
    )

    with commit():
        _rename(deal, "Acme 2027")

    [run] = _runs(org_a)
    assert (run.status, run.reason) == (DONE, "")
    assert [(step["status"], step["text"]) for step in run.steps] == [
        (SKIPPED, "This deal has no account"),
        (DONE, "Set Probability to 30 on Acme 2027"),
        (SKIPPED, "Nobody to notify"),
        (DONE, "Set Amount to 500 on Acme 2027"),
    ]
    deal.refresh_from_db()
    assert (deal.probability, deal.amount) == (30, Decimal("500"))


def test_an_unexpected_error_in_a_step_fails_the_rule_in_plain_words(
    org_a, owner, commit, caplog
):
    deal = _deal(org_a, probability=5)
    _rule(org_a, owner, [_set("probability", 30), _task()])

    with (
        patch("automation.actions.create_task", side_effect=RuntimeError("boom")),
        caplog.at_level(logging.ERROR, logger="automation.engine"),
        commit(),
    ):
        _rename(deal, "Acme 2027")

    [run] = _runs(org_a)
    assert (run.status, run.reason) == (FAILED, GENERIC)
    assert run.steps == [
        _step(0, "set_field", UNDONE, "Set Probability to 30 on Acme 2027"),
        _step(1, "create_task", FAILED, GENERIC),
    ]
    deal.refresh_from_db()
    assert deal.probability == 5
    assert not Task.objects.filter(org=org_a).exists()
    assert any(r.name == "automation.engine" for r in caplog.records)


def test_one_broken_rule_neither_raises_nor_stops_the_others(
    org_a, owner, commit, caplog
):
    deal = _deal(org_a)
    broken = _rule(org_a, owner, [_set("probability", 10)], name="Broken")
    # Stored JSON no editor could send, so the condition check itself raises.
    AutomationRule.objects.filter(pk=broken.pk).update(conditions={"field": "x"})
    _rule(org_a, owner, [_set("amount", 500)], name="Fine", position=1)

    with caplog.at_level(logging.ERROR, logger="automation.engine"), commit():
        _rename(deal, "Acme 2027")

    deal.refresh_from_db()
    assert (deal.name, deal.amount) == ("Acme 2027", Decimal("500"))
    assert [run.rule.name for run in _runs(org_a)] == ["Fine"]
    assert any(r.name == "automation.engine" for r in caplog.records)

    change = Change(org_a.id, "deal", deal.pk, "updated", {"name": ("A", "Acme 2027")})
    with patch("automation.engine.runnable", side_effect=RuntimeError("boom")):
        assert process([change]) is None


def test_a_change_the_record_no_longer_shows_sets_nothing_off(org_a, owner):
    deal = _deal(org_a)
    _rule(org_a, owner, [_set("probability", 30)], name="By name")
    by_amount = _rule(
        org_a,
        owner,
        [_set("probability", 40)],
        name="By amount",
        trigger={"event": "updated", "field": "amount", "to": None},
        position=1,
    )
    Opportunity.objects.filter(pk=deal.pk).update(amount=Decimal("700"))

    # The name was rolled back after it was captured; the amount stuck.
    process(
        [
            Change(
                org_a.id,
                "deal",
                deal.pk,
                "updated",
                {"name": ("Acme renewal", "Acme 2027"), "amount": (None, Decimal(700))},
            )
        ]
    )
    assert [run.rule for run in _runs(org_a)] == [by_amount]

    process([Change(org_a.id, "deal", deal.pk, "updated", {"name": ("A", "B")})])
    assert _runs(org_a).count() == 1
    deal.refresh_from_db()
    assert deal.probability == 40


def test_a_change_reaches_only_its_own_orgs_records(org_a, org_b, owner):
    with rls_org(org_b):
        other = _deal(org_b, name="Org B deal", probability=5)
    _rule(org_a, owner, [_set("probability", 30)])

    process(
        [Change(org_a.id, "deal", other.pk, "updated", {"name": ("Old", "Org B deal")})]
    )

    assert not _runs(org_a).exists()
    with rls_org(org_b):
        other.refresh_from_db()
        assert other.probability == 5


@pytest.mark.postgres_only
def test_each_change_runs_as_its_org_and_the_context_is_put_back(org_a, org_b, owner):
    if connection.vendor != "postgresql":
        pytest.skip("RLS context is a PostgreSQL setting")
    from automation import actions

    def current():
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('app.current_org', true)")
            return cursor.fetchone()[0]

    deal = _deal(org_a)
    _rename(deal, "Acme 2027")
    _rule(org_a, owner, [_set("probability", 30)])
    seen, real = [], actions.plan_action

    def plan_and_note(*args):
        seen.append(current())
        return real(*args)

    set_session_org(org_b.id)
    try:
        with patch("automation.engine.plan_action", side_effect=plan_and_note):
            process(
                [
                    Change(
                        org_a.id,
                        "deal",
                        deal.pk,
                        "updated",
                        {"name": ("Acme renewal", "Acme 2027")},
                    )
                ]
            )
        assert seen == [str(org_a.id)]
        assert current() == str(org_b.id)
    finally:
        restore_rls_context()
    assert _runs(org_a).get().status == DONE


# Limits and notices


def test_the_1001st_run_in_an_hour_is_counted_not_stored(org_a, owner, commit):
    other_admin = _member(org_a, "Ravi", role="ADMIN")
    _member(org_a, "Meera")
    rule = _rule(org_a, owner, [_set("probability", 30)])
    deals = [_deal(org_a, name=f"Deal {n}", probability=5) for n in range(3)]

    with _at_now():
        _fill_the_hour(rule, deals[0])
        for deal in deals:
            with commit():
                _rename(deal, f"{deal.name}, renamed")

    [row] = _runs(org_a).filter(status=SKIPPED)
    assert (row.rule, row.skipped_count, row.window_start) == (rule, 3, WINDOW)
    assert row.reason == "3 runs skipped: the org reached its hourly limit"
    assert _runs(org_a).exclude(status=SKIPPED).count() == RUNS_PER_HOUR
    notices = Notification.objects.filter(org=org_a, verb="automation.limit")
    assert sorted(n.recipient_id for n in notices) == sorted([owner.pk, other_admin.pk])
    for notice in notices:
        assert notice.data == {"window_start": WINDOW.isoformat()}
    for deal in deals:
        deal.refresh_from_db()
        assert deal.probability == 5


def test_past_the_limit_a_rule_whose_conditions_refuse_counts_nothing(
    org_a, owner, commit
):
    deal = _deal(org_a, probability=5)
    matches = _rule(org_a, owner, [_set("probability", 30)], name="Matches")
    _rule(
        org_a,
        owner,
        [_set("probability", 40)],
        name="Refuses",
        position=1,
        conditions=[{"field": "name", "op": "contains", "value": "nothing like it"}],
    )

    with _at_now():
        _fill_the_hour(matches, deal)
        with commit():
            _rename(deal, "Acme 2027")

    skipped = _runs(org_a).filter(status=SKIPPED)
    assert list(skipped.values_list("rule", "skipped_count")) == [(matches.pk, 1)]


def test_the_limit_notice_goes_once_per_org_per_window(org_a, owner, commit):
    deal = _deal(org_a)
    rule = _rule(org_a, owner, [_set("probability", 30)])
    # Another process crossed the limit at the same moment and told the admins.
    cache.add(f"automation-limit:{org_a.pk}:{WINDOW.isoformat()}", 1, 3600)

    with _at_now():
        _fill_the_hour(rule, deal)
        with commit():
            _rename(deal, "Acme 2027")

    assert _runs(org_a).get(status=SKIPPED).skipped_count == 1
    assert not Notification.objects.filter(org=org_a, verb="automation.limit").exists()


def test_another_orgs_runs_do_not_throttle_this_org(org_a, org_b, owner, commit):
    deal = _deal(org_a, probability=5)
    _rule(org_a, owner, [_set("probability", 30)])

    with _at_now():
        with rls_org(org_b):
            b_rule = _rule(org_b, _member(org_b, "Bo", role="ADMIN"), [])
            _fill_the_hour(b_rule, _deal(org_b))
        with commit():
            _rename(deal, "Acme 2027")

    assert [run.status for run in _runs(org_a)] == [DONE]
    deal.refresh_from_db()
    assert deal.probability == 30


def test_failure_notices_reach_the_owner_once_a_day(org_a, owner, commit):
    deal = _deal(org_a)
    rule = _rule(org_a, owner, [_set("stage", _won(deal))], name="Close it")

    def notices():
        found = Notification.objects.filter(org=org_a, verb="automation.failed")
        return list(found.order_by("created_at"))

    def a_day_later():
        AutomationRule.objects.filter(pk=rule.pk).update(
            last_failure_notice_at=timezone.now() - timedelta(hours=25)
        )

    for name in ("First", "Second"):
        with commit():
            _rename(deal, name)

    assert _runs(org_a).filter(status=FAILED).count() == 2
    [notice] = notices()
    assert (notice.recipient, notice.link) == (owner, f"/settings/automation/{rule.pk}")
    assert notice.data == {
        "rule": "Close it",
        "rule_id": str(rule.pk),
        "reason": NOT_CLOSED,
    }
    rule.refresh_from_db()
    assert rule.last_failure_notice_at is not None

    a_day_later()
    with commit():
        _rename(deal, "Third")
    assert len(notices()) == 2

    # An email that fails after its run was done is a failure too.
    a_day_later()
    run = _past_run(rule, deal, days=0)
    with patch("automation.tasks.EmailMultiAlternatives.send", side_effect=OSError):
        send_member_email(
            [str(owner.pk)],
            "Subject",
            "Text",
            f"/pipeline/{deal.pk}",
            str(org_a.pk),
            str(run.pk),
            0,
        )
    restore_rls_context()
    assert [n.data["reason"] for n in notices()] == [
        NOT_CLOSED,
        NOT_CLOSED,
        "The email could not be sent",
    ]


def test_a_rule_the_plan_hook_excludes_does_not_run(org_a, owner, commit):
    hook = NoRulesRun()
    register_plan_hook(hook)
    deal = _deal(org_a, probability=5)
    _rule(org_a, owner, [_set("probability", 30)], name="Deal rule")
    _rule(org_a, owner, [_task()], name="Lead rule", object_key="lead")
    off = _rule(org_a, owner, [_set("probability", 50)], name="Off")
    AutomationRule.objects.filter(pk=off.pk).update(is_active=False)

    with commit():
        _rename(deal, "Acme 2027")

    assert hook.asked == ["Deal rule", "Lead rule"]
    assert not _runs(org_a).exists()
    deal.refresh_from_db()
    assert deal.probability == 5


def test_old_runs_are_pruned_as_runs_are_written(org_a, org_b, owner, commit):
    deal = _deal(org_a)
    rule = _rule(org_a, owner, [_set("probability", 30)])
    old = _past_run(rule, deal, RUN_RETENTION_DAYS + 1)
    recent = _past_run(rule, deal, RUN_RETENTION_DAYS - 1)
    with rls_org(org_b):
        b_deal = _deal(org_b)
        b_rule = _rule(org_b, _member(org_b, "Bo", role="ADMIN"), [])
        b_old = _past_run(b_rule, b_deal, RUN_RETENTION_DAYS + 1)

    # The worker runs the queued task here, as soon as it is queued.
    with patch.object(prune_org_runs, "delay", side_effect=prune_org_runs) as queued:
        with commit():
            _rename(deal, "First")
        restore_rls_context()

        queued.assert_called_once_with(str(org_a.pk))
        remaining = set(_runs(org_a).values_list("pk", flat=True))
        assert old.pk not in remaining
        assert recent.pk in remaining
        assert len(remaining) == 2
        with rls_org(org_b):
            assert AutomationRun.objects.filter(pk=b_old.pk).exists()

        # Once a day per org: the next write today leaves this one for tomorrow.
        older = _past_run(rule, deal, RUN_RETENTION_DAYS + 5)
        with commit():
            _rename(deal, "Second")
        restore_rls_context()
        queued.assert_called_once()
        assert _runs(org_a).filter(pk=older.pk).exists()


def test_a_request_queues_the_prune_instead_of_running_it(
    admin_client, org_a, owner, django_capture_on_commit_callbacks
):
    deal = _deal(org_a)
    rule = _rule(org_a, owner, [_set("probability", 30)])
    old = _past_run(rule, deal, RUN_RETENTION_DAYS + 1)

    with (
        patch.object(prune_org_runs, "delay") as queued,
        django_capture_on_commit_callbacks(execute=True),
    ):
        response = admin_client.patch(
            f"/api/opportunities/{deal.pk}/", {"name": "Acme 2027"}, format="json"
        )

    assert response.status_code == 200, response.content
    queued.assert_called_once_with(str(org_a.pk))
    assert _runs(org_a).filter(pk=old.pk).exists()


def test_the_daily_job_prunes_every_orgs_old_runs(org_a, org_b, owner):
    deal = _deal(org_a)
    rule = _rule(org_a, owner, [])
    _past_run(rule, deal, RUN_RETENTION_DAYS + 1)
    recent = _past_run(rule, deal, RUN_RETENTION_DAYS - 1)
    with rls_org(org_b):
        b_deal = _deal(org_b)
        b_rule = _rule(org_b, _member(org_b, "Bo", role="ADMIN"), [])
        _past_run(b_rule, b_deal, RUN_RETENTION_DAYS + 1)

    assert prune_runs() == 2
    restore_rls_context()

    assert list(_runs(org_a).values_list("pk", flat=True)) == [recent.pk]
    with rls_org(org_b):
        assert not _runs(org_b).exists()
    assert app.conf.beat_schedule["prune-automation-runs"] == {
        "task": "automation.tasks.prune_runs",
        "schedule": crontab(hour=3, minute=50),
    }


# Try it on a record


def test_try_writes_nothing(org_a, owner, django_capture_on_commit_callbacks):
    asha, ravi = _member(org_a, "Asha"), _member(org_a, "Ravi")
    deal = _deal(org_a)
    deal.assigned_to.add(asha)
    endpoint = WebhookEndpoint.objects.create(
        org=org_a,
        url="https://hooks.example.com/in",
        events=["deal.updated"],
        created_by=owner.user,
    )
    rule = _rule(
        org_a,
        owner,
        [
            _set("name", "Renamed"),
            _set("city", "Pune", target="parent"),
            {
                "type": "assign",
                "people": [str(asha.pk), str(ravi.pk)],
                "mode": "rotate",
            },
            _task(assign_to="record"),
            {
                "type": "notify",
                "to": ["record_assignees"],
                "people": [],
                "message": "{name} moved",
            },
            {"type": "webhook", "endpoint": str(endpoint.pk)},
        ],
    )

    with (
        patch(EMAIL) as email,
        patch(DELIVER) as deliver,
        django_capture_on_commit_callbacks() as callbacks,
        CaptureQueriesContext(connection) as queries,
    ):
        steps = try_rule(rule, deal)

    assert steps == [
        {
            "action": 0,
            "type": "set_field",
            "status": "planned",
            "text": "Would set Deal name to 'Renamed' on Acme renewal",
        },
        {
            "action": 1,
            "type": "set_field",
            "status": "skipped",
            "text": "This deal has no account",
        },
        {
            "action": 2,
            "type": "assign",
            "status": "planned",
            "text": "Would assign Acme renewal to Asha by rotation",
        },
        {
            "action": 3,
            "type": "create_task",
            "status": "planned",
            "text": "Would create the task 'Call Acme renewal' for Asha",
        },
        {
            "action": 4,
            "type": "notify",
            "status": "planned",
            "text": "Would notify Asha",
        },
        {
            "action": 5,
            "type": "webhook",
            "status": "planned",
            "text": "Would send Acme renewal to hooks.example.com",
        },
    ]
    assert [q["sql"] for q in queries.captured_queries if _is_write(q["sql"])] == []
    assert callbacks == []
    email.assert_not_called()
    deliver.assert_not_called()
    for model in (
        AutomationRun,
        Notification,
        Task,
        WebhookDelivery,
        AutomationRotation,
        Activity,
    ):
        assert not model.objects.filter(org=org_a).exists(), model
    deal.refresh_from_db()
    assert deal.name == "Acme renewal"


def test_try_answers_validation_errors_as_failed_steps(org_a, owner):
    gone = _member(org_a, "Gone")
    deal = _deal(org_a)
    rule = _rule(
        org_a,
        owner,
        [
            _set("probability", "lots"),
            {"type": "assign", "people": [str(gone.pk)], "mode": "replace"},
            _task(),
        ],
    )
    Profile.objects.filter(pk=gone.pk).update(is_active=False)

    first = "actions[0].value: Enter a number."
    assert try_rule(rule, deal) == [
        _step(0, "set_field", FAILED, first),
        _step(
            1,
            "assign",
            FAILED,
            "actions[1].people: Each person must be an active member of this org.",
        ),
        _step(2, "create_task", FAILED, first),
    ]


def test_try_plans_a_rule_nobody_switched_on_as_the_admin_trying_it(org_a, owner):
    deal = _deal(org_a)
    rule = _rule(org_a, None, [_task()])

    assert try_rule(rule, deal, owner=owner) == [
        {
            "action": 0,
            "type": "create_task",
            "status": "planned",
            "text": "Would create the task 'Call Acme renewal' for Olga",
        }
    ]
