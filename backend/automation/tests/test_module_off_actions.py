"""A rule's Create a task step while Tasks is off: a stored one is skipped, with
the module message, and the rule's other steps still run; a new one is refused,
and the catalogue does not offer it."""

from unittest.mock import patch

import pytest

from automation.models import AutomationRule, AutomationRun
from automation.validation import new_task_step_errors
from common.models import Notification
from common.testing import set_modules_off
from leads.models import Lead
from tasks.models import Task

RULES = "/api/automation/rules/"
CATALOGUE = "/api/automation/catalogue/"
EMAIL = "automation.actions.send_member_email.delay"
OFF = "Tasks is switched off for this organization."
TASK_STEP = {
    "type": "create_task",
    "title": "Call {name}",
    "due_in_days": None,
    "priority": "High",
    "assign_to": "owner",
    "person": None,
}
NOTIFY_STEP = {"type": "notify", "to": ["admins"], "people": [], "message": "New lead"}


@pytest.fixture
def commit(django_capture_on_commit_callbacks):
    return lambda: django_capture_on_commit_callbacks(execute=True)


def _body(actions):
    return {
        "name": "New lead follow-up",
        "object_key": "lead",
        "trigger": {"event": "created", "field": None, "to": None},
        "match": "all",
        "conditions": [],
        "actions": actions,
        "is_active": True,
    }


def _rule(client):
    response = client.post(RULES, _body([TASK_STEP, NOTIFY_STEP]), format="json")
    assert response.status_code == 201, response.content
    return response.json()


def _new_lead(client):
    response = client.post(
        "/api/leads/",
        {"title": "Inbound", "first_name": "Pat", "email": "pat@example.com"},
        format="json",
    )
    assert response.status_code == 200, response.content


def _steps(org):
    [run] = AutomationRun.objects.filter(org=org)
    return run, {step["type"]: step for step in run.steps}


def test_create_task_is_skipped_while_tasks_is_off(admin_client, org_a, commit):
    _rule(admin_client)
    set_modules_off(org_a, "tasks")

    with patch(EMAIL), commit():
        _new_lead(admin_client)

    run, steps = _steps(org_a)
    assert run.status == "done"
    assert steps["create_task"]["status"] == "skipped"
    assert steps["create_task"]["text"] == OFF
    assert steps["notify"]["status"] == "done"
    assert not Task.objects.filter(org=org_a).exists()
    assert Notification.objects.filter(org=org_a, verb="automation.message").exists()
    assert Lead.objects.filter(org=org_a).count() == 1


def test_create_task_runs_when_tasks_is_on(admin_client, org_a, commit):
    _rule(admin_client)

    with patch(EMAIL), commit():
        _new_lead(admin_client)

    run, steps = _steps(org_a)
    assert run.status == "done"
    assert steps["create_task"]["status"] == "done"
    assert Task.objects.filter(org=org_a, title__startswith="Call ").count() == 1


def test_the_catalogue_offers_create_task_only_while_tasks_is_on(admin_client, org_a):
    def actions():
        response = admin_client.get(CATALOGUE)
        assert response.status_code == 200
        return response.json()["actions"]

    assert "create_task" in actions()
    set_modules_off(org_a, "tasks")
    assert sorted(actions()) == ["assign", "notify", "set_field", "webhook"]


def test_a_new_create_task_step_is_refused_while_tasks_is_off(admin_client, org_a):
    set_modules_off(org_a, "tasks")
    body = _body([NOTIFY_STEP, TASK_STEP])

    response = admin_client.post(RULES, body, format="json")

    assert response.status_code == 400
    assert response.json() == {"errors": {"actions[1].type": [OFF]}}
    assert not AutomationRule.objects.filter(org=org_a).exists()
    set_modules_off(org_a)
    assert admin_client.post(RULES, body, format="json").status_code == 201


def test_a_stored_create_task_step_is_kept_while_tasks_is_off(admin_client, org_a):
    rule = _rule(admin_client)
    stored_task, stored_notify = rule["actions"]
    url = f"{RULES}{rule['id']}/"
    set_modules_off(org_a, "tasks")

    kept = admin_client.patch(
        url, {"actions": [stored_notify, stored_task]}, format="json"
    )
    assert kept.status_code == 200, kept.content

    another = {**stored_task, "title": "Email {name}"}
    added = admin_client.patch(
        url, {"actions": [stored_notify, stored_task, another]}, format="json"
    )
    assert added.status_code == 400
    assert added.json() == {"errors": {"actions[2].type": [OFF]}}
    assert AutomationRule.objects.get(pk=rule["id"]).actions == [
        stored_notify,
        stored_task,
    ]
    [listed] = admin_client.get(RULES).json()["results"]
    assert listed["status"] == "on"


def _task(title="Call {name}", **extra):
    return {"type": "create_task", "title": title, **extra}


def _refused(org, sent, stored):
    return new_task_step_errors(org, sent, stored)


def test_a_stored_task_step_without_person_matches_one_sent_with_person_null(org_a):
    set_modules_off(org_a, "tasks")
    stored = [_task(priority="High")]
    sent = [_task(priority="High", person=None, due_in_days=None)]

    assert _refused(org_a, sent, stored) == {}


def test_a_second_copy_of_a_stored_task_step_is_refused_at_its_index(org_a):
    set_modules_off(org_a, "tasks")
    step = _task()

    assert _refused(org_a, [step, step], [step]) == {"actions[1].type": [OFF]}


def test_stored_task_steps_may_change_places(org_a):
    set_modules_off(org_a, "tasks")
    first, second = _task("A"), _task("B")

    assert _refused(org_a, [second, first], [first, second]) == {}


def test_a_changed_title_is_a_new_step(org_a):
    set_modules_off(org_a, "tasks")

    assert _refused(org_a, [_task("Email")], [_task("Call")]) == {
        "actions[0].type": [OFF]
    }


def test_nothing_is_refused_while_tasks_is_on(org_a):
    assert _refused(org_a, [_task(), _task()], []) == {}
