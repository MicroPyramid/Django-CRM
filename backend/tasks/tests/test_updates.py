"""`update_task` and `create_task`, the write paths the task views and
automation rules share.

Called here as a rule calls them: with a bare object carrying only `profile`.
"""

from types import SimpleNamespace
from unittest.mock import call, patch

import pytest

from accounts.models import Account
from common.models import Profile, Tags, Teams, User
from contacts.models import Contact
from leads.models import Lead
from tasks.models import Task
from tasks.updates import create_task, update_task

pytestmark = pytest.mark.django_db

MAIL = "tasks.updates.send_email_to_assigned_user.delay"
BODY = {"title": "Call back", "status": "New", "priority": "High"}


@pytest.fixture
def request_obj(admin_profile):
    return SimpleNamespace(profile=admin_profile)


@pytest.fixture
def other_profile(org_a):
    user = User.objects.create_user(email="other@test.com", password="testpass123")
    return Profile.objects.create(user=user, org=org_a, role="USER", is_active=True)


@pytest.fixture
def task(org_a, admin_user, admin_profile):
    task = Task.objects.create(
        title="Task",
        status="New",
        priority="High",
        description="Ring them",
        org=org_a,
        created_by=admin_user,
    )
    task.contacts.add(
        Contact.objects.create(first_name="Linked", last_name="Person", org=org_a)
    )
    task.teams.add(Teams.objects.create(name="Field", description="-", org=org_a))
    task.tags.add(Tags.objects.create(name="Warm", org=org_a))
    task.assigned_to.add(admin_profile)
    return task


def _ids(*profiles):
    return sorted(str(p.id) for p in profiles)


def test_a_partial_update_writes_only_the_named_fields(
    request_obj, task, django_capture_on_commit_callbacks
):
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_task(request_obj, task, {"status": "In Progress"})
    assert errors is None
    task.refresh_from_db()
    assert task.status == "In Progress"
    assert task.title == "Task"
    assert task.priority == "High"
    assert task.description == "Ring them"
    assert task.contacts.count() == 1
    assert task.teams.count() == 1
    assert task.tags.count() == 1
    assert task.assigned_to.count() == 1
    mail.assert_not_called()


def test_an_invalid_value_writes_nothing_and_returns_errors(request_obj, task):
    errors = update_task(
        request_obj, task, {"priority": "Whenever", "status": "In Progress"}
    )
    assert "priority" in errors
    task.refresh_from_db()
    assert task.priority == "High"
    assert task.status == "New"


def test_assignees_replace_and_email_only_new_people(
    request_obj,
    task,
    org_a,
    user_profile,
    other_profile,
    django_capture_on_commit_callbacks,
):
    task.assigned_to.add(user_profile)
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_task(
            request_obj, task, {"assigned_to": _ids(user_profile, other_profile)}
        )
    assert errors is None
    assert set(task.assigned_to.all()) == {user_profile, other_profile}
    mail.assert_called_once_with(_ids(other_profile), str(task.id), str(org_a.id))


def test_another_orgs_assignee_is_ignored_or_refused(
    request_obj,
    task,
    org_a,
    user_profile,
    profile_b,
    django_capture_on_commit_callbacks,
):
    """Ignored, as the PATCH does today: the write succeeds without them."""
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_task(
            request_obj, task, {"assigned_to": _ids(user_profile, profile_b)}
        )
    assert errors is None
    assert list(task.assigned_to.all()) == [user_profile]
    mail.assert_called_once_with(_ids(user_profile), str(task.id), str(org_a.id))


def test_create_task_links_its_parent_and_assigns(
    request_obj, org_a, admin_user, user_profile, django_capture_on_commit_callbacks
):
    account = Account.objects.create(name="Difference Engines", org=org_a)
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        task, errors = create_task(
            request_obj,
            {
                **BODY,
                "account": str(account.id),
                "assigned_to": _ids(user_profile),
            },
        )
    assert errors is None
    task.refresh_from_db()
    assert task.title == "Call back"
    assert task.account == account
    assert task.org == org_a
    assert task.created_by == admin_user
    assert list(task.assigned_to.all()) == [user_profile]
    mail.assert_called_once_with(_ids(user_profile), str(task.id), str(org_a.id))


def test_a_task_with_two_parents_is_refused(
    request_obj, org_a, django_capture_on_commit_callbacks
):
    account = Account.objects.create(name="Difference Engines", org=org_a)
    lead = Lead.objects.create(first_name="Ada", last_name="Lovelace", org=org_a)
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        task, errors = create_task(
            request_obj,
            {**BODY, "account": str(account.id), "lead": str(lead.id)},
        )
    assert task is None
    assert "account" in errors
    assert not Task.objects.filter(title="Call back").exists()
    mail.assert_not_called()


def test_another_orgs_parent_is_refused(request_obj, org_b):
    account = Account.objects.create(name="Elsewhere", org=org_b)
    task, errors = create_task(request_obj, {**BODY, "account": str(account.id)})
    assert task is None
    assert "account" in errors
    assert not Task.objects.filter(title="Call back").exists()


def test_the_email_waits_for_the_commit(
    request_obj, task, org_a, other_profile, django_capture_on_commit_callbacks
):
    with patch(MAIL) as mail:
        with django_capture_on_commit_callbacks() as callbacks:
            update_task(request_obj, task, {"assigned_to": _ids(other_profile)})
            created, _errors = create_task(
                request_obj, {**BODY, "assigned_to": _ids(other_profile)}
            )
        mail.assert_not_called()
        for callback in callbacks:
            callback()
    assert mail.call_args_list == [
        call(_ids(other_profile), str(task.id), str(org_a.id)),
        call(_ids(other_profile), str(created.id), str(org_a.id)),
    ]
