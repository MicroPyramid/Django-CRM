"""A rule's actions: each one planned without writing, then applied as the owner."""

import hashlib
import hmac
import logging
import uuid
from datetime import UTC, date, datetime
from smtplib import SMTPRecipientsRefused
from unittest.mock import patch

import pytest
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext

from accounts.models import Account
from automation import links
from automation.actions import (
    Planned,
    RunContext,
    StepFailed,
    StepSkipped,
    plan_action,
    render,
)
from automation.adapters.deals import DealAdapter
from automation.adapters.leads import LeadAdapter
from automation.links import LinkSpec, register_link_hook
from automation.models import (
    DONE,
    FAILED,
    AutomationRotation,
    AutomationRule,
    AutomationRun,
)
from automation.objects import adapter_for
from automation.tasks import send_member_email
from common.links import frontend_url
from common.models import Notification, Org, Profile, User
from common.object_registry import object_for_key
from common.tests.object_records import make_record
from conftest import rls_org
from opportunity.models import DealPipeline, DealStage, Opportunity
from tasks.models import Task
from webhooks import events
from webhooks.models import SLACK, WebhookDelivery, WebhookEndpoint
from webhooks.tasks import build_request

EMAIL = "automation.actions.send_member_email.delay"
DEAL_ASSIGNED = "opportunity.updates.send_email_to_assigned_user.delay"
DELIVER = "webhooks.emit.deliver_webhook.delay"
MARKUP = "<img src=x onerror=alert(1)>"


@pytest.fixture(autouse=True)
def restore_link_hooks():
    saved = list(links._HOOKS)
    yield
    links._HOOKS[:] = saved


class FakeLinkHook:
    def __init__(self, object_key, spec, records):
        self.object_key, self.spec, self.found = object_key, spec, records

    def specs(self, org, object_key):
        return [self.spec] if object_key == self.object_key else []

    def records(self, org, object_key, record, spec_id):
        return self.found


PROPERTIES = LinkSpec("in:property.deals", "Properties linked through Deals", "account")


def _member(org, name, *, role="USER", active=True, user_active=True):
    user = User.objects.create_user(
        email=f"{name.lower()}@example.com",
        password="testpass123",
        name=name,
        is_active=user_active,
    )
    return Profile.objects.create(user=user, org=org, role=role, is_active=active)


def _rule(org, owner, actions=(), name="Deal won", object_key="deal"):
    return AutomationRule.objects.create(
        org=org,
        name=name,
        object_key=object_key,
        trigger={"event": "updated", "field": None, "to": None},
        actions=list(actions),
        owner=owner,
        is_active=True,
    )


def _ctx(rule, record, *, adapter=None, run_id=None):
    adapter = adapter or adapter_for(rule.org, rule.object_key)
    return RunContext(rule.org, rule, record, adapter, rule.owner, run_id)


def _deal(org, name="Acme renewal", **values):
    pipeline = DealPipeline.default_for(org)
    return Opportunity.objects.create(
        org=org, name=name, pipeline=pipeline, stage="QUALIFICATION", **values
    )


def _assignees(record):
    record.refresh_from_db()
    return list(record.assigned_to.order_by("user__name"))


def _set_field(target, field, value):
    return {"type": "set_field", "target": target, "field": field, "value": value}


def _task(assign_to="owner", person=None, title="Call {name}", due_in_days=None):
    return {
        "type": "create_task",
        "title": title,
        "due_in_days": due_in_days,
        "priority": "High",
        "assign_to": assign_to,
        "person": person,
    }


def _notify(to=(), people=(), message="{name} is won"):
    return {
        "type": "notify",
        "to": list(to),
        "people": list(people),
        "message": message,
    }


def _endpoint(org, creator, **values):
    return WebhookEndpoint.objects.create(
        org=org,
        url="https://hooks.example.com/in",
        events=["deal.updated"],
        created_by=creator.user,
        **values,
    )


def _is_write(sql):
    statement = sql.lstrip().upper()
    return statement.startswith(("INSERT", "UPDATE", "DELETE")) or "FOR UPDATE" in (
        statement
    )


# Planning


def test_planning_writes_nothing(
    org_a, admin_profile, django_capture_on_commit_callbacks
):
    asha, ravi = _member(org_a, "Asha"), _member(org_a, "Ravi")
    account = make_record("account", org_a)
    deal = _deal(org_a, account=account)
    deal.assigned_to.add(asha)
    endpoint = _endpoint(org_a, admin_profile)
    register_link_hook(FakeLinkHook("deal", PROPERTIES, [account]))
    actions = [
        _set_field("record", "name", "Renamed"),
        _set_field("parent", "city", "Pune"),
        _set_field(PROPERTIES.id, "city", "Goa"),
        {"type": "assign", "people": [str(asha.pk), str(ravi.pk)], "mode": "rotate"},
        {"type": "assign", "people": [str(ravi.pk)], "mode": "replace"},
        _task(assign_to="record", due_in_days=3),
        _notify(to=["record_assignees", "admins", f"linked:{PROPERTIES.id}"]),
        {"type": "webhook", "endpoint": str(endpoint.pk)},
    ]
    rule = _rule(org_a, admin_profile, actions)
    ctx = _ctx(rule, deal, run_id=uuid.uuid4())
    city = account.city

    with (
        patch(EMAIL) as email,
        patch(DELIVER) as deliver,
        django_capture_on_commit_callbacks() as callbacks,
        CaptureQueriesContext(connection) as queries,
    ):
        planned = [plan_action(ctx, i, action) for i, action in enumerate(actions)]

    assert all(isinstance(step, Planned) for step in planned)
    assert all(step.text.startswith("Would ") for step in planned)
    assert [q["sql"] for q in queries.captured_queries if _is_write(q["sql"])] == []
    assert callbacks == []
    email.assert_not_called()
    deliver.assert_not_called()
    for model in (Notification, Task, WebhookDelivery, AutomationRotation):
        assert not model.objects.filter(org=org_a).exists(), model
    deal.refresh_from_db()
    account.refresh_from_db()
    assert (deal.name, account.city) == ("Acme renewal", city)
    assert _assignees(deal) == [asha]


# Set a field


def test_set_field_on_the_parent(org_a, admin_profile):
    account = Account.objects.create(org=org_a, name="Acme", city="Delhi")
    deal = _deal(org_a, account=account)
    action = _set_field("parent", "city", "Pune")
    rule = _rule(org_a, admin_profile, [action])

    planned = plan_action(_ctx(rule, deal), 0, action)
    assert planned.text == "Would set City to 'Pune' on Acme"
    account.refresh_from_db()
    assert account.city == "Delhi"

    assert planned.apply() == "Set City to 'Pune' on Acme"
    account.refresh_from_db()
    assert account.city == "Pune"


def test_set_field_on_a_deal_with_no_account_is_skipped(org_a, admin_profile):
    deal = _deal(org_a)
    action = _set_field("parent", "city", "Pune")
    rule = _rule(org_a, admin_profile, [action])
    with pytest.raises(StepSkipped) as skipped:
        plan_action(_ctx(rule, deal), 0, action)
    assert skipped.value.text == "This deal has no account"


def test_clearing_a_field_and_choice_labels_read_as_labels(org_a, admin_profile):
    deal = _deal(org_a, amount=10)
    won = DealStage.objects.get(pipeline=deal.pipeline, code="CLOSED_WON")
    ctx = _ctx(_rule(org_a, admin_profile), deal)
    assert plan_action(ctx, 0, _set_field("record", "amount", None)).text == (
        "Would clear Amount on Acme renewal"
    )
    assert plan_action(ctx, 0, _set_field("record", "stage", str(won.pk))).text == (
        "Would set Stage to Closed Won on Acme renewal"
    )
    assert plan_action(ctx, 0, _set_field("record", "amount", None)).apply() == (
        "Cleared Amount on Acme renewal"
    )
    deal.refresh_from_db()
    assert deal.amount is None


def test_a_refused_write_fails_the_step_with_the_services_message(org_a, admin_profile):
    deal = _deal(org_a, closed_on=date(2026, 10, 1))
    won = DealStage.objects.get(pipeline=deal.pipeline, code="CLOSED_WON")
    action = _set_field("record", "stage", str(won.pk))
    rule = _rule(org_a, admin_profile, [action])

    planned = plan_action(_ctx(rule, deal), 0, action)
    with pytest.raises(StepFailed) as failed:
        planned.apply()
    assert failed.value.text == "A won deal has to record what it was worth."
    deal.refresh_from_db()
    assert deal.stage == "QUALIFICATION"


def test_set_field_on_linked_records_sets_each_one(org_a, admin_profile):
    deal = _deal(org_a)
    one = Account.objects.create(org=org_a, name="12 Park Lane")
    two = Account.objects.create(org=org_a, name="4 Elm Road")
    hook = FakeLinkHook("deal", PROPERTIES, [one, two])
    register_link_hook(hook)
    action = _set_field(PROPERTIES.id, "city", "Goa")
    ctx = _ctx(_rule(org_a, admin_profile, [action]), deal)

    planned = plan_action(ctx, 0, action)
    assert planned.text == "Would set City to 'Goa' on 12 Park Lane and 4 Elm Road"
    assert planned.apply() == "Set City to 'Goa' on 12 Park Lane and 4 Elm Road"
    assert set(Account.objects.filter(org=org_a).values_list("city", flat=True)) == {
        "Goa"
    }

    hook.found = []
    with pytest.raises(StepSkipped) as skipped:
        plan_action(ctx, 0, action)
    assert skipped.value.text == "This deal has no properties linked through deals"


def test_more_than_100_linked_records_fails(org_a, admin_profile):
    deal = _deal(org_a)
    account = make_record("account", org_a)
    hook = FakeLinkHook("deal", PROPERTIES, [account] * 101)
    register_link_hook(hook)
    ctx = _ctx(_rule(org_a, admin_profile), deal)
    message = "101 linked records: an action may reach at most 100"
    for action in (
        _set_field(PROPERTIES.id, "city", "Goa"),
        _notify(to=[f"linked:{PROPERTIES.id}"]),
    ):
        with pytest.raises(StepFailed) as failed:
            plan_action(ctx, 0, action)
        assert failed.value.text == message

    hook.found = [account] * 100
    assert plan_action(ctx, 0, _set_field(PROPERTIES.id, "city", "Goa")).text


# Assign


def test_rotation_takes_turns_and_skips_inactive_people(org_a, admin_profile):
    asha = _member(org_a, "Asha")
    left = _member(org_a, "Left", active=False)
    ravi = _member(org_a, "Ravi")
    locked_out = _member(org_a, "Locked", user_active=False)
    action = {
        "type": "assign",
        "people": [str(p.pk) for p in (asha, left, ravi, locked_out)],
        "mode": "rotate",
    }
    rule = _rule(org_a, admin_profile, [action])
    deal = _deal(org_a)
    ctx = _ctx(rule, deal)

    for expected in (asha, ravi, asha):
        planned = plan_action(ctx, 0, action)
        name = expected.user.name
        assert planned.text == f"Would assign Acme renewal to {name} by rotation"
        assert planned.apply() == f"Assigned Acme renewal to {name} by rotation"
        assert _assignees(deal) == [expected]
    rotation = AutomationRotation.objects.get(org=org_a, rule=rule, action_index=0)
    assert rotation.next_index == 3

    Profile.objects.filter(pk__in=[asha.pk, ravi.pk]).update(is_active=False)
    with pytest.raises(StepFailed) as failed:
        plan_action(ctx, 0, action)
    assert failed.value.text == "None of the chosen people is an active member"


def test_the_rotation_cursor_is_kept_per_action(org_a, admin_profile):
    asha, ravi = _member(org_a, "Asha"), _member(org_a, "Ravi")
    action = {
        "type": "assign",
        "people": [str(asha.pk), str(ravi.pk)],
        "mode": "rotate",
    }
    rule = _rule(org_a, admin_profile, [action, action])
    ctx = _ctx(rule, _deal(org_a))
    plan_action(ctx, 0, action).apply()
    assert "Asha" in plan_action(ctx, 1, action).text
    assert "Ravi" in plan_action(ctx, 0, action).text


def test_replace_assign_replaces(org_a, admin_profile):
    asha, ravi, meera = (_member(org_a, n) for n in ("Asha", "Ravi", "Meera"))
    deal = _deal(org_a)
    deal.assigned_to.add(asha, ravi)
    action = {"type": "assign", "people": [str(meera.pk)], "mode": "replace"}
    planned = plan_action(_ctx(_rule(org_a, admin_profile, [action]), deal), 0, action)
    assert planned.text == "Would assign Acme renewal to Meera"
    assert _assignees(deal) == [asha, ravi]
    assert planned.apply() == "Assigned Acme renewal to Meera"
    assert _assignees(deal) == [meera]
    assert not AutomationRotation.objects.filter(org=org_a).exists()


# Create a task

# 03:00 UTC on 23 October is 20:00 on 22 October in Los Angeles.
UTC_IS_TOMORROW = datetime(2026, 10, 23, 3, 0, tzinfo=UTC)


def test_create_task_due_date_uses_the_org_timezone(org_a, admin_profile):
    action = _task(due_in_days=2)
    for zone, due in (("America/Los_Angeles", 24), ("UTC", 25)):
        Org.objects.filter(pk=org_a.pk).update(timezone=zone)
        org_a.refresh_from_db()
        rule = _rule(org_a, admin_profile, [action])
        deal = _deal(org_a, name=zone)
        with patch("django.utils.timezone.now", return_value=UTC_IS_TOMORROW):
            plan_action(_ctx(rule, deal), 0, action).apply()
        task = Task.objects.get(org=org_a, opportunity=deal)
        assert task.due_date == date(2026, 10, due), zone


class UnlinkedAdapter(LeadAdapter):
    """A record kind a task cannot link to, as a custom record is."""

    def task_parent(self, record):
        return {}


@pytest.mark.parametrize(
    "key, column",
    [
        ("deal", "opportunity"),
        ("lead", "lead"),
        ("account", "account"),
        ("ticket", "case"),
        ("contact", None),
        ("unlinked", None),
    ],
)
def test_create_task_links_the_record(key, column, org_a, admin_profile, settings):
    settings.FRONTEND_URL = "https://app.example.com"
    object_key = "lead" if key == "unlinked" else key
    record = make_record(object_key, org_a)
    adapter = (
        UnlinkedAdapter(object_for_key(org_a, "lead")) if key == "unlinked" else None
    )
    action = _task(title="Kick-off call: {name}")
    rule = _rule(org_a, admin_profile, [action], object_key=object_key)
    ctx = _ctx(rule, record, adapter=adapter)

    planned = plan_action(ctx, 0, action)
    title = f"Kick-off call: {ctx.adapter.name(record)}"
    assert planned.text == f"Would create the task '{title}' for admin"
    assert planned.apply() == f"Created the task '{title}' for admin"

    task = Task.objects.get(org=org_a)
    assert (task.title, task.status, task.priority) == (title, "New", "High")
    assert task.due_date is None
    assert list(task.assigned_to.all()) == [admin_profile]
    assert task.created_by == admin_profile.user
    columns = ("opportunity", "lead", "account", "case")
    parents = {c: getattr(task, f"{c}_id") for c in columns}
    assert {c for c, pk in parents.items() if pk} == ({column} if column else set())
    if column:
        assert parents[column] == record.pk
    assert list(task.contacts.all()) == ([record] if key == "contact" else [])
    if key == "unlinked":
        assert task.description == frontend_url(f"/leads/{record.pk}")
    else:
        assert not task.description


def test_create_task_skips_people_who_cannot_open_the_record(org_a, admin_profile):
    asha, meera = _member(org_a, "Asha"), _member(org_a, "Meera")
    account = make_record("account", org_a)
    account.assigned_to.add(meera)
    deal = _deal(org_a, account=account)
    deal.assigned_to.add(asha)
    ctx = _ctx(_rule(org_a, admin_profile), deal)

    with pytest.raises(StepSkipped) as skipped:
        plan_action(ctx, 0, _task(assign_to="parent"))
    assert skipped.value.text == "Skipped Meera: cannot open this deal"

    planned = plan_action(ctx, 0, _task(assign_to="record"))
    assert planned.text == "Would create the task 'Call Acme renewal' for Asha"

    Opportunity.objects.filter(pk=deal.pk).update(account=None)
    deal.refresh_from_db()
    with pytest.raises(StepSkipped) as skipped:
        plan_action(ctx, 0, _task(assign_to="parent"))
    assert skipped.value.text == "This deal has no account"
    assert not Task.objects.filter(org=org_a).exists()


# Notify


def test_notify_skips_people_who_cannot_open_the_record(org_a, admin_profile):
    meera = _member(org_a, "Meera")
    deal = _deal(org_a)
    action = _notify(to=["admins"], people=[str(meera.pk)])
    planned = plan_action(_ctx(_rule(org_a, admin_profile, [action]), deal), 0, action)
    assert "Skipped" in planned.text
    assert "Meera" in planned.text
    assert "cannot open this deal" in planned.text
    assert planned.text == "Would notify admin. Skipped Meera: cannot open this deal"

    with patch(EMAIL):
        assert planned.apply() == "Notified admin. Skipped Meera: cannot open this deal"
    assert list(
        Notification.objects.filter(org=org_a).values_list("recipient", flat=True)
    ) == [admin_profile.pk]


def test_notify_with_nobody_left_is_skipped(org_a, admin_profile):
    meera, ravi = _member(org_a, "Meera"), _member(org_a, "Ravi")
    _member(org_a, "Gone", active=False)
    deal = _deal(org_a)
    ctx = _ctx(_rule(org_a, admin_profile), deal)

    with pytest.raises(StepSkipped) as skipped:
        plan_action(ctx, 0, _notify(people=[str(ravi.pk), str(meera.pk)]))
    assert skipped.value.text == "Skipped Ravi and Meera: cannot open this deal"

    with pytest.raises(StepSkipped) as skipped:
        plan_action(ctx, 0, _notify(to=["parent_assignees"]))
    assert skipped.value.text == "This deal has no account"

    with pytest.raises(StepSkipped) as skipped:
        plan_action(ctx, 0, _notify(to=["record_assignees", "record_creator"]))
    assert skipped.value.text == "Nobody to notify"
    assert not Notification.objects.filter(org=org_a).exists()


def test_notify_writes_the_message_as_data(
    org_a, admin_profile, django_capture_on_commit_callbacks
):
    asha = _member(org_a, "Asha")
    deal = _deal(org_a, name="Acme")
    deal.assigned_to.add(asha)
    action = _notify(to=["record_assignees", "parent_assignees"])
    rule = _rule(org_a, admin_profile, [action, action])
    run_id = uuid.uuid4()
    planned = plan_action(_ctx(rule, deal, run_id=run_id), 1, action)
    assert planned.text == "Would notify Asha. This deal has no account"

    with patch(EMAIL) as email:
        with django_capture_on_commit_callbacks() as callbacks:
            assert planned.apply() == "Notified Asha. This deal has no account"
        email.assert_not_called()
        assert len(callbacks) == 1
        callbacks[0]()

    path = f"/pipeline/{deal.pk}"
    email.assert_called_once_with(
        [str(asha.pk)],
        "Acme is won",
        "Acme is won",
        path,
        str(org_a.pk),
        str(run_id),
        1,
    )
    notice = Notification.objects.get(org=org_a)
    assert notice.recipient == asha
    assert notice.verb == "automation.message"
    assert notice.actor == admin_profile
    assert (notice.entity_type, notice.entity_id) == ("Opportunity", deal.pk)
    assert (notice.entity_name, notice.link) == ("Acme", path)
    assert notice.data == {"message": "Acme is won", "rule": "Deal won"}


def test_an_email_that_cannot_be_queued_marks_its_step_failed(
    org_a, admin_profile, django_capture_on_commit_callbacks
):
    asha = _member(org_a, "Asha")
    deal = _deal(org_a)
    deal.assigned_to.add(asha)
    action = _notify(to=["record_assignees"])
    rule = _rule(org_a, admin_profile, [action])
    run = _run(rule, deal, [_step(0, "notify", "Notified Asha")])
    planned = plan_action(_ctx(rule, deal, run_id=run.pk), 0, action)

    with patch(EMAIL, side_effect=OSError("broker down")):
        with django_capture_on_commit_callbacks(execute=True):
            planned.apply()
    run.refresh_from_db()
    assert (run.status, run.reason) == (FAILED, "The email could not be sent")
    assert run.steps[0]["status"] == FAILED


# Placeholders


def test_render_replaces_name_only():
    assert render("{name} {owner} {{name}}", "Acme") == "Acme {owner} {Acme}"
    assert render("No placeholder", "Acme") == "No placeholder"
    assert render("{name}", "{name}") == "{name}"
    assert render("{0} %s {name!r}", "Acme") == "{0} %s {name!r}"


def test_markup_in_a_name_stays_text(org_a, admin_profile):
    asha = _member(org_a, "Asha")
    deal = _deal(org_a, name=MARKUP)
    deal.assigned_to.add(asha)
    ctx = _ctx(_rule(org_a, admin_profile), deal)

    with patch(EMAIL):
        plan_action(ctx, 0, _notify(to=["record_assignees"])).apply()
    plan_action(ctx, 1, _task(title="Call {name}")).apply()

    assert Notification.objects.get(org=org_a).data["message"] == f"{MARKUP} is won"
    assert Task.objects.get(org=org_a).title == f"Call {MARKUP}"


def test_the_member_email_goes_to_active_members_with_the_text_escaped(
    org_a, org_b, mailoutbox, settings
):
    settings.FRONTEND_URL = "https://app.example.com"
    asha = _member(org_a, "Asha")
    gone = _member(org_a, "Gone", active=False)
    with rls_org(org_b):
        outsider = _member(org_b, "Outsider")
    text = f"{MARKUP} & co"

    send_member_email(
        [str(asha.pk), str(gone.pk), str(outsider.pk)],
        "Subject",
        text,
        "/pipeline/abc",
        str(org_a.pk),
    )

    assert [message.to for message in mailoutbox] == [["asha@example.com"]]
    message = mailoutbox[0]
    assert message.subject == "Subject"
    assert text in message.body
    assert "https://app.example.com/pipeline/abc" in message.body
    (html, mimetype), *_ = message.alternatives
    assert mimetype == "text/html"
    assert "&lt;img src=x onerror=alert(1)&gt; &amp; co" in html
    assert MARKUP not in html
    assert 'href="https://app.example.com/pipeline/abc"' in html


def _run(rule, record, steps):
    return AutomationRun.objects.create(
        org=rule.org,
        rule=rule,
        object_key=rule.object_key,
        record_id=record.pk,
        record_name=str(record),
        status=DONE,
        chain_id=uuid.uuid4(),
        steps=steps,
    )


def _step(action, kind, text):
    return {"action": action, "type": kind, "status": DONE, "text": text}


def test_an_email_that_fails_marks_its_step_failed(org_a, admin_profile, caplog):
    asha = _member(org_a, "Asha")
    deal = _deal(org_a)
    rule = _rule(org_a, admin_profile)
    first = _step(0, "set_field", "Set Amount to 5 on Acme renewal")
    run = _run(rule, deal, [first, _step(1, "notify", "Notified Asha")])
    refused = SMTPRecipientsRefused({"asha@example.com": (550, b"No such user")})

    with (
        patch("automation.tasks.EmailMultiAlternatives.send", side_effect=refused),
        caplog.at_level(logging.DEBUG),
    ):
        send_member_email(
            [str(asha.pk)],
            "Subject",
            "A private message",
            f"/pipeline/{deal.pk}",
            str(org_a.pk),
            str(run.pk),
            1,
        )

    run.refresh_from_db()
    assert (run.status, run.reason) == (FAILED, "The email could not be sent")
    assert run.steps[0] == first
    assert run.steps[1]["status"] == FAILED
    assert run.steps[1]["text"] == "Notified Asha. The email could not be sent"
    assert f"Automation email to profile {asha.pk} failed: SMTPRecipientsRefused" in (
        caplog.text
    )
    assert "asha@example.com" not in caplog.text
    assert "A private message" not in caplog.text


# Webhook


def test_webhook_queues_a_signed_delivery_to_the_endpoint(
    org_a, admin_profile, django_capture_on_commit_callbacks
):
    deal = _deal(org_a)
    endpoint = _endpoint(org_a, admin_profile)
    action = {"type": "webhook", "endpoint": str(endpoint.pk)}
    rule = _rule(org_a, admin_profile, [action])

    planned = plan_action(_ctx(rule, deal), 0, action)
    assert planned.text == "Would send Acme renewal to hooks.example.com"
    with patch(DELIVER) as deliver:
        with django_capture_on_commit_callbacks(execute=True):
            assert planned.apply() == "Sent Acme renewal to hooks.example.com"

    delivery = WebhookDelivery.objects.get(org=org_a)
    deliver.assert_called_once_with(str(delivery.pk), str(org_a.pk))
    assert (delivery.endpoint, delivery.event) == (endpoint, "rule.triggered")
    payload = delivery.payload
    assert payload["event"] == "rule.triggered"
    assert payload["org_id"] == str(org_a.pk)
    assert payload["data"] == {
        "rule": {"id": str(rule.pk), "name": "Deal won"},
        "object": "deal",
        "record": events.to_json(events.deal_data(deal)),
    }

    body, headers = build_request(delivery)
    parts = dict(
        item.split("=", 1) for item in headers["X-BottleCRM-Signature"].split(",")
    )
    expected = hmac.new(
        endpoint.secret.encode(), f"{parts['t']}.".encode() + body, hashlib.sha256
    ).hexdigest()
    assert hmac.compare_digest(parts["v1"], expected)


class NoPayloadAdapter(DealAdapter):
    def webhook_data(self, record):
        return None


def test_a_webhook_needs_an_active_json_endpoint_and_a_payload(
    org_a, org_b, admin_profile, profile_b
):
    deal = _deal(org_a)
    ctx = _ctx(_rule(org_a, admin_profile), deal)
    with rls_org(org_b):
        theirs = _endpoint(org_b, profile_b)
    refused = (
        _endpoint(org_a, admin_profile, is_active=False),
        _endpoint(org_a, admin_profile, format=SLACK),
        theirs,
    )
    for endpoint in refused:
        with pytest.raises(StepFailed) as failed:
            plan_action(ctx, 0, {"type": "webhook", "endpoint": str(endpoint.pk)})
        assert failed.value.text == "This webhook endpoint is switched off or gone"
    with pytest.raises(StepFailed):
        plan_action(ctx, 0, {"type": "webhook", "endpoint": "not-an-id"})

    live = {"type": "webhook", "endpoint": str(_endpoint(org_a, admin_profile).pk)}
    entry = object_for_key(org_a, "deal")
    with pytest.raises(StepFailed) as failed:
        plan_action(_ctx(ctx.rule, deal, adapter=NoPayloadAdapter(entry)), 0, live)
    assert failed.value.text == (
        "Webhooks for this kind of record come in a later version"
    )
    assert not WebhookDelivery.objects.filter(org=org_a).exists()


# In order, as the engine runs a rule


def _apply_in_order(ctx, actions):
    """Plan every action, then apply each in order in one transaction."""
    planned = [plan_action(ctx, i, action) for i, action in enumerate(actions)]
    texts = []
    with transaction.atomic():
        for step in planned:
            try:
                texts.append(step.apply())
            except StepSkipped as exc:
                texts.append(f"skipped: {exc.text}")
    return planned, texts


def test_assign_then_notify_reaches_the_new_assignee_only(
    org_a, admin_profile, django_capture_on_commit_callbacks
):
    meera, bob = _member(org_a, "Meera"), _member(org_a, "Bob")
    deal = _deal(org_a, name="Acme")
    deal.assigned_to.add(meera)
    actions = [
        {"type": "assign", "people": [str(bob.pk)], "mode": "replace"},
        _notify(to=["record_assignees"], message="{name} is yours"),
        _notify(people=[str(meera.pk)]),
    ]
    ctx = _ctx(_rule(org_a, admin_profile, actions), deal, run_id=uuid.uuid4())

    with (
        patch(EMAIL) as email,
        patch(DEAL_ASSIGNED),
        django_capture_on_commit_callbacks(execute=True),
    ):
        planned, texts = _apply_in_order(ctx, actions)

    assert [step.text for step in planned[1:]] == [
        "Would notify Meera",
        "Would notify Meera",
    ]
    assert texts == [
        "Assigned Acme to Bob",
        "Notified Bob",
        "skipped: Skipped Meera: cannot open this deal",
    ]
    recipients = Notification.objects.filter(org=org_a).values_list("recipient")
    assert list(recipients) == [(bob.pk,)]
    email.assert_called_once()
    assert email.call_args.args[:2] == ([str(bob.pk)], "Acme is yours")


def test_rotate_then_create_a_task_gives_it_to_the_person_rotation_picked(
    org_a, admin_profile
):
    asha, ravi = _member(org_a, "Asha"), _member(org_a, "Ravi")
    lead = make_record("lead", org_a)
    actions = [
        {"type": "assign", "people": [str(asha.pk), str(ravi.pk)], "mode": "rotate"},
        _task(assign_to="record"),
    ]
    ctx = _ctx(_rule(org_a, admin_profile, actions, object_key="lead"), lead)

    planned, texts = _apply_in_order(ctx, actions)

    assert planned[1].text == "Would create the task 'Call Rec' for nobody yet"
    assert texts == [
        "Assigned Rec to Asha by rotation",
        "Created the task 'Call Rec' for Asha",
    ]
    task = Task.objects.get(org=org_a)
    assert (task.lead, list(task.assigned_to.all())) == (lead, [asha])


def test_nobody_reached_after_the_earlier_steps_is_skipped_at_apply(
    org_a, admin_profile
):
    lead = make_record("lead", org_a)
    left = _member(org_a, "Left")
    actions = [
        {"type": "assign", "people": [str(left.pk)], "mode": "replace"},
        _task(assign_to="record"),
    ]
    ctx = _ctx(_rule(org_a, admin_profile, actions, object_key="lead"), lead)
    planned = [plan_action(ctx, i, action) for i, action in enumerate(actions)]
    with transaction.atomic():
        planned[0].apply()
        Profile.objects.filter(pk=left.pk).update(is_active=False)
        with pytest.raises(StepSkipped) as skipped:
            planned[1].apply()
    assert skipped.value.text == "Nobody to give the task to"
    assert not Task.objects.filter(org=org_a).exists()


def test_steps_on_one_record_keep_each_others_changes(org_a, admin_profile):
    asha = _member(org_a, "Asha")
    account = Account.objects.create(org=org_a, name="Acme", city="Delhi")
    deal = _deal(org_a, account=account)
    actions = [
        _set_field("parent", "city", "Pune"),
        _set_field("parent", "name", "Acme Ltd"),
        _set_field("record", "name", "Acme renewal 2027"),
        {"type": "assign", "people": [str(asha.pk)], "mode": "replace"},
        _task(assign_to="record"),
    ]
    ctx = _ctx(_rule(org_a, admin_profile, actions), deal)

    planned, texts = _apply_in_order(ctx, actions)

    account.refresh_from_db()
    assert (account.city, account.name) == ("Pune", "Acme Ltd")
    deal.refresh_from_db()
    assert deal.name == "Acme renewal 2027"
    assert _assignees(deal) == [asha]
    assert planned[4].text == "Would create the task 'Call Acme renewal' for nobody yet"
    assert texts[4] == "Created the task 'Call Acme renewal 2027' for Asha"
    assert Task.objects.get(org=org_a).title == "Call Acme renewal 2027"


def test_a_long_name_is_cut_to_fit_the_task_title(org_a, admin_profile):
    deal = _deal(org_a, name="N" * 250)
    action = _task(title="Call {name}")
    plan_action(_ctx(_rule(org_a, admin_profile, [action]), deal), 0, action).apply()
    title = Task.objects.get(org=org_a).title
    assert len(title) == 200
    assert title.startswith("Call NNN")


def test_people_from_another_org_are_never_reached(
    org_a, org_b, admin_profile, profile_b, django_capture_on_commit_callbacks
):
    asha = _member(org_a, "Asha")
    deal = _deal(org_a)
    deal.assigned_to.add(asha)
    theirs = str(profile_b.pk)
    ctx = _ctx(_rule(org_a, admin_profile), deal)

    with pytest.raises(StepFailed) as failed:
        plan_action(ctx, 0, {"type": "assign", "people": [theirs], "mode": "replace"})
    assert failed.value.text == "None of the chosen people is an active member"
    with pytest.raises(StepSkipped) as skipped:
        plan_action(ctx, 1, _notify(people=[theirs]))
    assert skipped.value.text == "Nobody to notify"
    with pytest.raises(StepSkipped) as skipped:
        plan_action(ctx, 2, _task(assign_to="person", person=theirs))
    assert skipped.value.text == "Nobody to give the task to"

    rotate = {"type": "assign", "people": [theirs, str(asha.pk)], "mode": "rotate"}
    for _ in range(2):
        plan_action(ctx, 0, rotate).apply()
    notify = _notify(to=["record_assignees"], people=[theirs])
    with patch(EMAIL) as email, django_capture_on_commit_callbacks(execute=True):
        assert plan_action(ctx, 1, notify).apply() == "Notified Asha"
    plan_action(ctx, 2, _task(assign_to="record")).apply()

    assert _assignees(deal) == [asha]
    assert not deal.assigned_to.filter(pk=profile_b.pk).exists()
    assert not Notification.objects.filter(recipient=profile_b).exists()
    assert not Task.objects.filter(assigned_to=profile_b).exists()
    assert list(Task.objects.get(org=org_a).assigned_to.all()) == [asha]
    email.assert_called_once()
    assert email.call_args.args[0] == [str(asha.pk)]
