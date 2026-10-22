"""`update_account`, the one write path the account PATCH and automation rules
share.

Called here as a rule calls it: with a bare object carrying only `profile`.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from accounts.models import Account
from accounts.updates import update_account
from common.models import Profile, Tags, Teams, User
from contacts.models import Contact

pytestmark = pytest.mark.django_db

MAIL = "accounts.updates.send_email_to_assigned_user.delay"


@pytest.fixture
def request_obj(admin_profile):
    return SimpleNamespace(profile=admin_profile)


@pytest.fixture
def other_profile(org_a):
    user = User.objects.create_user(email="other@test.com", password="testpass123")
    return Profile.objects.create(user=user, org=org_a, role="USER", is_active=True)


@pytest.fixture
def account(org_a, admin_profile):
    account = Account.objects.create(
        name="Difference Engines", industry="ADVERTISING", org=org_a
    )
    account.contacts.add(
        Contact.objects.create(first_name="Linked", last_name="Person", org=org_a)
    )
    account.teams.add(Teams.objects.create(name="Field", description="-", org=org_a))
    account.tags.add(Tags.objects.create(name="Warm", org=org_a))
    account.assigned_to.add(admin_profile)
    return account


def test_a_partial_update_writes_only_the_named_fields(
    request_obj, account, django_capture_on_commit_callbacks
):
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_account(request_obj, account, {"city": "London"})
    assert errors is None
    account.refresh_from_db()
    assert account.city == "London"
    assert account.name == "Difference Engines"
    assert account.industry == "ADVERTISING"
    assert account.contacts.count() == 1
    assert account.teams.count() == 1
    assert account.tags.count() == 1
    assert account.assigned_to.count() == 1
    mail.assert_not_called()


def test_an_invalid_value_writes_nothing_and_returns_errors(request_obj, account):
    errors = update_account(
        request_obj, account, {"annual_revenue": "-1", "city": "London"}
    )
    assert "annual_revenue" in errors
    account.refresh_from_db()
    assert account.annual_revenue is None
    assert account.city is None


def test_assignees_replace_and_email_only_new_people(
    request_obj,
    account,
    org_a,
    user_profile,
    other_profile,
    django_capture_on_commit_callbacks,
):
    account.assigned_to.add(user_profile)
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_account(
            request_obj,
            account,
            {"assigned_to": [str(user_profile.id), str(other_profile.id)]},
        )
    assert errors is None
    assert set(account.assigned_to.all()) == {user_profile, other_profile}
    mail.assert_called_once_with([other_profile.id], account.id, str(org_a.id))


def test_another_orgs_assignee_is_ignored_or_refused(
    request_obj,
    account,
    org_a,
    user_profile,
    profile_b,
    django_capture_on_commit_callbacks,
):
    """Ignored, as the PATCH does today: the write succeeds without them."""
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_account(
            request_obj,
            account,
            {"assigned_to": [str(user_profile.id), str(profile_b.id)]},
        )
    assert errors is None
    assert list(account.assigned_to.all()) == [user_profile]
    mail.assert_called_once_with([user_profile.id], account.id, str(org_a.id))


def test_the_email_waits_for_the_commit(
    request_obj, account, org_a, other_profile, django_capture_on_commit_callbacks
):
    with patch(MAIL) as mail:
        with django_capture_on_commit_callbacks() as callbacks:
            update_account(
                request_obj, account, {"assigned_to": [str(other_profile.id)]}
            )
        mail.assert_not_called()
        for callback in callbacks:
            callback()
    mail.assert_called_once_with([other_profile.id], account.id, str(org_a.id))
