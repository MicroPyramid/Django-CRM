"""`update_lead`, the one write path the lead PATCH and automation rules share.

Called here as a rule calls it: with a bare object carrying only `profile`.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from common.models import Profile, Tags, Teams, User
from contacts.models import Contact
from leads.models import Lead
from leads.updates import update_lead

pytestmark = pytest.mark.django_db

MAIL = "leads.updates.send_email_to_assigned_user.delay"
REFUSAL = {"status": ["A lead is converted from its page, not by an edit."]}


@pytest.fixture
def request_obj(admin_profile):
    return SimpleNamespace(profile=admin_profile)


@pytest.fixture
def other_profile(org_a):
    user = User.objects.create_user(email="other@test.com", password="testpass123")
    return Profile.objects.create(user=user, org=org_a, role="USER", is_active=True)


@pytest.fixture
def lead(org_a, admin_profile):
    lead = Lead.objects.create(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        status="in process",
        job_title="Analyst",
        org=org_a,
    )
    lead.contacts.add(
        Contact.objects.create(first_name="Linked", last_name="Person", org=org_a)
    )
    lead.teams.add(Teams.objects.create(name="Field", description="-", org=org_a))
    lead.tags.add(Tags.objects.create(name="Warm", org=org_a))
    lead.assigned_to.add(admin_profile)
    return lead


def test_a_partial_update_writes_only_the_named_fields(
    request_obj, lead, django_capture_on_commit_callbacks
):
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_lead(request_obj, lead, {"job_title": "Chief Analyst"})
    assert errors is None
    lead.refresh_from_db()
    assert lead.job_title == "Chief Analyst"
    assert lead.first_name == "Ada"
    assert lead.status == "in process"
    assert lead.contacts.count() == 1
    assert lead.teams.count() == 1
    assert lead.tags.count() == 1
    assert lead.assigned_to.count() == 1
    mail.assert_not_called()


def test_an_invalid_value_writes_nothing_and_returns_errors(request_obj, lead):
    errors = update_lead(
        request_obj, lead, {"status": "converted", "job_title": "Chief Analyst"}
    )
    assert errors == REFUSAL
    lead.refresh_from_db()
    assert lead.status == "in process"
    assert lead.job_title == "Analyst"


def test_is_converted_is_refused_as_well(request_obj, lead):
    errors = update_lead(request_obj, lead, {"is_converted": True})
    assert errors == REFUSAL
    lead.refresh_from_db()
    assert lead.status == "in process"


def test_a_serializer_error_writes_nothing(request_obj, lead):
    errors = update_lead(
        request_obj, lead, {"probability": 250, "job_title": "Chief Analyst"}
    )
    assert "probability" in errors
    lead.refresh_from_db()
    assert lead.job_title == "Analyst"


def test_assignees_replace_and_email_only_new_people(
    request_obj,
    lead,
    org_a,
    admin_profile,
    user_profile,
    other_profile,
    django_capture_on_commit_callbacks,
):
    lead.assigned_to.add(user_profile)
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_lead(
            request_obj,
            lead,
            {"assigned_to": [str(user_profile.id), str(other_profile.id)]},
        )
    assert errors is None
    assert set(lead.assigned_to.all()) == {user_profile, other_profile}
    mail.assert_called_once_with([other_profile.id], lead.id, str(org_a.id))


def test_another_orgs_assignee_is_ignored_or_refused(
    request_obj,
    lead,
    org_a,
    user_profile,
    profile_b,
    django_capture_on_commit_callbacks,
):
    """Ignored, as the PATCH does today: the write succeeds without them."""
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_lead(
            request_obj,
            lead,
            {"assigned_to": [str(user_profile.id), str(profile_b.id)]},
        )
    assert errors is None
    assert list(lead.assigned_to.all()) == [user_profile]
    mail.assert_called_once_with([user_profile.id], lead.id, str(org_a.id))


def test_the_email_waits_for_the_commit(
    request_obj, lead, org_a, other_profile, django_capture_on_commit_callbacks
):
    with patch(MAIL) as mail:
        with django_capture_on_commit_callbacks() as callbacks:
            update_lead(request_obj, lead, {"assigned_to": [str(other_profile.id)]})
        mail.assert_not_called()
        for callback in callbacks:
            callback()
    mail.assert_called_once_with([other_profile.id], lead.id, str(org_a.id))
