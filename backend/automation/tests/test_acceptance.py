"""Whole flows, from the save that sets a rule off to what the rule leaves behind.

Rules are built through the API as an admin would build them, and the saves
that set them off go through the app's own paths: the deal edit form, the
board, a public web form, an emailed ticket and a spreadsheet import.
"""

import csv
import io
from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone

from accounts.models import Account
from automation import engine
from automation.models import DONE, AutomationRun
from cases.inbound.parser import parse_raw_email
from cases.inbound.pipeline import ingest
from cases.models import InboundMailbox, RoutingRule
from common.management.commands.seed_data import Command as SeedData
from common.models import Notification, Org, Profile, User
from common.testing import _make_authenticated_client
from leads.models import Lead
from opportunity.models import DealPipeline, Opportunity
from tasks.models import Task
from webforms.models import WebForm, WebFormField
from webhooks.models import WebhookDelivery, WebhookEndpoint

RULES = "/api/automation/rules/"
EMAIL = "automation.actions.send_member_email.delay"
DELIVER = "webhooks.emit.deliver_webhook.delay"
CREATED = {"event": "created", "field": None, "to": None}
NAME_CHANGES = {"event": "updated", "field": "name", "to": None}
TO_WON = {"event": "updated", "field": "stage_kind", "to": "won"}
FAR_EAST = "Pacific/Kiritimati"


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


def _client(profile):
    return _make_authenticated_client(profile.user, profile.org, profile)


def _build(client, name, object_key, trigger, actions, conditions=()):
    """Save a rule and switch it on through the API, as an admin's editor does."""
    response = client.post(
        RULES,
        {
            "name": name,
            "object_key": object_key,
            "trigger": trigger,
            "match": "all",
            "conditions": list(conditions),
            "actions": list(actions),
            "is_active": True,
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    return response.json()["id"]


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


def _task(title="Call {name}", assign_to="owner", due_in_days=None):
    return {
        "type": "create_task",
        "title": title,
        "due_in_days": due_in_days,
        "priority": "High",
        "assign_to": assign_to,
        "person": None,
    }


def _web_form(org):
    form = WebForm.objects.create(
        name="Contact us", org=org, is_published=True, lead_source="other"
    )
    WebFormField.objects.create(
        form=form,
        org=org,
        order=0,
        source=WebFormField.SOURCE_LEAD,
        lead_field="email",
        label="Email",
        is_required=True,
    )
    return form


def _submit(client, form, email):
    response = client.post(
        f"/api/public/forms/{form.org_id}/{form.id}/submit/",
        {"email": email},
        format="json",
    )
    assert response.status_code == 200, response.content


def _raw_email(message_id, subject):
    return "\r\n".join(
        [
            "From: Customer <user@example.com>",
            "To: support@acme.com",
            f"Subject: {subject}",
            "Date: Thu, 22 Oct 2026 12:00:00 +0000",
            f"Message-ID: {message_id}",
            "MIME-Version: 1.0",
            'Content-Type: text/plain; charset="utf-8"',
            "",
            "I cannot log in.",
        ]
    )


def _csv(rows):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["first_name", "last_name", "email"])
    writer.writerows(rows)
    return SimpleUploadedFile("leads.csv", buf.getvalue().encode("utf-8"), "text/csv")


def _runs(org):
    return AutomationRun.objects.filter(org=org)


def test_deal_won_onboarding(admin_client, org_a, owner, admin_user, commit):
    org_a.timezone = FAR_EAST
    org_a.save(update_fields=["timezone"])
    asha, ravi, meera = (_member(org_a, n) for n in ("Asha", "Ravi", "Meera"))
    ines = _member(org_a, "Ines", role="ADMIN")
    account = Account.objects.create(org=org_a, name="Acme")
    account.assigned_to.add(ravi, meera, ines)
    deal = _deal(org_a, account=account, amount=12000, closed_on=timezone.localdate())
    deal.assigned_to.add(asha, ravi)
    _build(
        admin_client,
        "Deal won: onboarding",
        "deal",
        TO_WON,
        [
            _task("Kick-off call: {name}", assign_to="record", due_in_days=2),
            {
                "type": "notify",
                "to": ["parent_assignees"],
                "people": [],
                "message": "{name} is won. Time to say hello.",
            },
        ],
        conditions=[{"field": "amount", "op": "gt", "value": 0}],
    )

    with patch(EMAIL) as email, commit():
        response = _client(asha).patch(
            f"/api/opportunities/{deal.pk}/", {"stage": "CLOSED_WON"}, format="json"
        )

    assert response.status_code == 200, response.content
    task = Task.objects.get(org=org_a)
    assert task.title == "Kick-off call: Acme renewal"
    due = datetime.now(ZoneInfo(FAR_EAST)).date() + timedelta(days=2)
    assert task.due_date == due
    assert set(task.assigned_to.all()) == {asha, ravi}
    assert (task.opportunity, task.created_by) == (deal, admin_user)

    notices = Notification.objects.filter(org=org_a, verb="automation.message")
    assert {notice.recipient for notice in notices} == {ravi, ines}
    assert len(notices) == 2
    for notice in notices:
        assert notice.data == {
            "message": "Acme renewal is won. Time to say hello.",
            "rule": "Deal won: onboarding",
        }
    email.assert_called_once()
    assert sorted(email.call_args.args[0]) == sorted([str(ravi.pk), str(ines.pk)])

    [run] = _runs(org_a)
    assert (run.status, run.record_id) == (DONE, deal.pk)
    assert [(step["type"], step["status"]) for step in run.steps] == [
        ("create_task", DONE),
        ("notify", DONE),
    ]
    assert run.steps[1]["text"].endswith("Skipped Meera: cannot open this deal")


def test_dragging_a_deal_to_won_then_editing_runs_once(admin_client, org_a, owner):
    deal = _deal(org_a, amount=5000)
    _build(
        admin_client,
        "Deal won: kick-off",
        "deal",
        TO_WON,
        [_task("Kick-off call: {name}")],
    )

    with patch("automation.engine.process", wraps=engine.process) as processed:
        moved = admin_client.patch(
            f"/api/opportunities/{deal.pk}/move/",
            {"column_id": "CLOSED_WON"},
            format="json",
        )
        assert moved.status_code == 200, moved.content
        # The whole record back, unchanged stage included, as an edit form posts it.
        edited = admin_client.patch(
            f"/api/opportunities/{deal.pk}/",
            {
                "description": "Signed on the call",
                "name": "Acme renewal, signed",
                "stage": "CLOSED_WON",
            },
            format="json",
        )
        assert edited.status_code == 200, edited.content

    # The edit did reach the engine, as a change that is not a move into Won.
    [move], [edit] = (call.args[0] for call in processed.call_args_list)
    assert "stage_kind" in move.changes
    assert set(edit.changes) == {"name"}
    assert [run.status for run in _runs(org_a)] == [DONE]
    assert list(Task.objects.filter(org=org_a).values_list("title", flat=True)) == [
        "Kick-off call: Acme renewal"
    ]


def test_a_web_form_lead_is_assigned_in_rotation(
    unauthenticated_client, admin_client, org_a, owner
):
    asha, ravi = _member(org_a, "Asha"), _member(org_a, "Ravi")
    form = _web_form(org_a)
    _build(
        admin_client,
        "Share web leads",
        "lead",
        CREATED,
        [{"type": "assign", "people": [str(asha.pk), str(ravi.pk)], "mode": "rotate"}],
    )

    _submit(unauthenticated_client, form, "pat@example.com")
    _submit(unauthenticated_client, form, "sam@example.com")

    first = Lead.objects.get(org=org_a, email="pat@example.com")
    second = Lead.objects.get(org=org_a, email="sam@example.com")
    assert list(first.assigned_to.all()) == [asha]
    assert list(second.assigned_to.all()) == [ravi]
    runs = _runs(org_a).order_by("created_at")
    assert [(run.record_id, run.status) for run in runs] == [
        (first.pk, DONE),
        (second.pk, DONE),
    ]


def test_an_emailed_ticket_sets_off_a_ticket_created_rule(
    admin_client, org_a, owner, commit
):
    asha = _member(org_a, "Asha")
    routing = RoutingRule.objects.create(
        org=org_a, name="Everything to Asha", strategy="direct", stop_processing=True
    )
    routing.target_assignees.set([asha])
    _build(
        admin_client,
        "Assigned tickets are urgent",
        "ticket",
        CREATED,
        [_set("priority", "Urgent")],
        conditions=[{"field": "assigned_to", "op": "not_empty", "value": None}],
    )
    mailbox = InboundMailbox.objects.create(
        org=org_a, address="support@acme.com", provider="ses"
    )

    with commit():
        result = ingest(
            parse_raw_email(_raw_email("<m1@example.com>", "Login")), mailbox
        )

    assert result.created_case
    ticket = result.case
    ticket.refresh_from_db()
    assert list(ticket.assigned_to.all()) == [asha]
    assert ticket.priority == "Urgent"
    [run] = _runs(org_a)
    assert (run.record_id, run.status) == (ticket.pk, DONE)

    # Without routing the new ticket has nobody, so the condition refuses it.
    RoutingRule.objects.filter(pk=routing.pk).update(is_active=False)
    with commit():
        result = ingest(
            parse_raw_email(_raw_email("<m2@example.com>", "Billing")), mailbox
        )
    unrouted = result.case
    unrouted.refresh_from_db()
    assert not unrouted.assigned_to.exists()
    assert unrouted.priority != "Urgent"
    assert _runs(org_a).count() == 1


def test_a_rules_change_reaches_webhooks_in_the_same_request(
    admin_client, org_a, owner, admin_user, commit
):
    endpoint = WebhookEndpoint.objects.create(
        org=org_a,
        url="https://hooks.example.com/in",
        events=["deal.updated"],
        created_by=admin_user,
    )
    deal = _deal(org_a, probability=5)
    _build(
        admin_client,
        "Renamed deals firm up",
        "deal",
        NAME_CHANGES,
        [_set("probability", 42)],
    )

    with patch(DELIVER) as deliver, commit():
        response = admin_client.patch(
            f"/api/opportunities/{deal.pk}/", {"name": "Acme 2027"}, format="json"
        )

    assert response.status_code == 200, response.content
    [delivery] = WebhookDelivery.objects.filter(org=org_a)
    assert (delivery.endpoint, delivery.event) == (endpoint, "deal.updated")
    data = delivery.payload["data"]
    assert (data["name"], data["probability"]) == ("Acme 2027", 42)
    deliver.assert_called_once_with(str(delivery.pk), str(org_a.pk))


def test_a_csv_import_creates_no_tasks(admin_client, org_a, owner, commit):
    _build(admin_client, "Call every new lead", "lead", CREATED, [_task()])

    response = admin_client.post(
        "/api/leads/import/commit/",
        {"file": _csv([["Ada", "Byte", "ada@x.io"], ["Bo", "Lee", "bo@x.io"]])},
        format="multipart",
    )

    assert response.status_code == 200, response.content
    assert response.json()["created"] == 2
    assert Lead.objects.filter(org=org_a).count() == 2
    assert not Task.objects.filter(org=org_a).exists()
    assert not _runs(org_a).exists()

    # The rule is live: a lead saved any other way gets its task.
    with commit():
        Lead.objects.create(org=org_a, title="Walk-in")
    assert list(Task.objects.filter(org=org_a).values_list("title", flat=True)) == [
        "Call Walk-in"
    ]


def test_the_seed_data_command_creates_no_tasks(admin_client, org_a, owner, commit):
    _build(admin_client, "Call every new lead", "lead", CREATED, [_task()])
    # The command fills the org it names first, "MicroPyramid".
    Org.objects.filter(pk=org_a.pk).update(name="MicroPyramid")
    counts = {"--leads": 3, "--accounts": 1, "--contacts": 2, "--opportunities": 1}
    counts |= {"--cases": 1, "--tasks": 0, "--goals": 0, "--users-per-org": 0}
    counts |= {"--products": 1, "--invoices": 0, "--estimates": 0}
    counts |= {"--recurring-invoices": 0, "--invoice-templates": 1}
    args = [str(part) for pair in counts.items() for part in pair]

    # Its SQL sets PostgreSQL's row-level security context, which SQLite lacks.
    with commit(), patch.object(SeedData, "set_rls_context"):
        call_command(
            "seed_data", "--email", owner.user.email, *args, stdout=io.StringIO()
        )

    assert Lead.objects.filter(org=org_a).count() == 3
    assert not Task.objects.filter(org=org_a).exists()
    assert not _runs(org_a).exists()

    with commit():
        Lead.objects.create(org=org_a, title="Walk-in")
    assert list(Task.objects.filter(org=org_a).values_list("title", flat=True)) == [
        "Call Walk-in"
    ]
