"""`update_contact`, the one write path the contact PATCH and automation rules
share.

Called here as a rule calls it: with a bare object carrying only `profile`.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from common.models import Profile, Tags, Teams, User
from contacts.models import Contact
from contacts.updates import update_contact

pytestmark = pytest.mark.django_db

MAIL = "contacts.updates.send_email_to_assigned_user.delay"


@pytest.fixture
def request_obj(admin_profile):
    return SimpleNamespace(profile=admin_profile)


@pytest.fixture
def other_profile(org_a):
    user = User.objects.create_user(email="other@test.com", password="testpass123")
    return Profile.objects.create(user=user, org=org_a, role="USER", is_active=True)


@pytest.fixture
def contact(org_a, admin_profile):
    contact = Contact.objects.create(
        first_name="Jo",
        last_name="Contact",
        email="jo@example.com",
        title="Buyer",
        org=org_a,
    )
    contact.teams.add(Teams.objects.create(name="Field", description="-", org=org_a))
    contact.tags.add(Tags.objects.create(name="Warm", org=org_a))
    contact.assigned_to.add(admin_profile)
    return contact


def test_a_partial_update_writes_only_the_named_fields(
    request_obj, contact, django_capture_on_commit_callbacks
):
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_contact(request_obj, contact, {"title": "Head Buyer"})
    assert errors is None
    contact.refresh_from_db()
    assert contact.title == "Head Buyer"
    assert contact.first_name == "Jo"
    assert contact.email == "jo@example.com"
    assert contact.teams.count() == 1
    assert contact.tags.count() == 1
    assert contact.assigned_to.count() == 1
    mail.assert_not_called()


def test_an_invalid_value_writes_nothing_and_returns_errors(request_obj, contact):
    errors = update_contact(
        request_obj, contact, {"email": "not-an-address", "title": "Head Buyer"}
    )
    assert "email" in errors
    contact.refresh_from_db()
    assert contact.email == "jo@example.com"
    assert contact.title == "Buyer"


def test_assignees_replace_and_email_only_new_people(
    request_obj,
    contact,
    org_a,
    user_profile,
    other_profile,
    django_capture_on_commit_callbacks,
):
    contact.assigned_to.add(user_profile)
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_contact(
            request_obj,
            contact,
            {"assigned_to": [str(user_profile.id), str(other_profile.id)]},
        )
    assert errors is None
    assert set(contact.assigned_to.all()) == {user_profile, other_profile}
    mail.assert_called_once_with([other_profile.id], contact.id, str(org_a.id))


def test_another_orgs_assignee_is_ignored_or_refused(
    request_obj,
    contact,
    org_a,
    user_profile,
    profile_b,
    django_capture_on_commit_callbacks,
):
    """Ignored, as the PATCH does today: the write succeeds without them."""
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_contact(
            request_obj,
            contact,
            {"assigned_to": [str(user_profile.id), str(profile_b.id)]},
        )
    assert errors is None
    assert list(contact.assigned_to.all()) == [user_profile]
    mail.assert_called_once_with([user_profile.id], contact.id, str(org_a.id))


def test_the_email_waits_for_the_commit(
    request_obj, contact, org_a, other_profile, django_capture_on_commit_callbacks
):
    with patch(MAIL) as mail:
        with django_capture_on_commit_callbacks() as callbacks:
            update_contact(
                request_obj, contact, {"assigned_to": [str(other_profile.id)]}
            )
        mail.assert_not_called()
        for callback in callbacks:
            callback()
    mail.assert_called_once_with([other_profile.id], contact.id, str(org_a.id))
