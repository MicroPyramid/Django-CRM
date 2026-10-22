"""`update_deal`, the one write path the deal PATCH and automation rules share.

Called here as a rule calls it: with a bare object carrying only `profile`.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from common.models import Profile, Tags, Teams, User
from contacts.models import Contact
from opportunity.models import Opportunity
from opportunity.updates import update_deal

pytestmark = pytest.mark.django_db

MAIL = "opportunity.updates.send_email_to_assigned_user.delay"


@pytest.fixture
def request_obj(admin_profile):
    return SimpleNamespace(profile=admin_profile)


@pytest.fixture
def other_profile(org_a):
    user = User.objects.create_user(email="other@test.com", password="testpass123")
    return Profile.objects.create(user=user, org=org_a, role="USER", is_active=True)


@pytest.fixture
def deal(org_a, admin_profile):
    deal = Opportunity.objects.create(
        name="Big deal", stage="QUALIFICATION", probability=20, org=org_a
    )
    deal.contacts.add(
        Contact.objects.create(first_name="Linked", last_name="Person", org=org_a)
    )
    deal.teams.add(Teams.objects.create(name="Field", description="-", org=org_a))
    deal.tags.add(Tags.objects.create(name="Warm", org=org_a))
    deal.assigned_to.add(admin_profile)
    return deal


def test_a_partial_update_writes_only_the_named_fields(
    request_obj, deal, django_capture_on_commit_callbacks
):
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_deal(request_obj, deal, {"probability": 60})
    assert errors is None
    deal.refresh_from_db()
    assert deal.probability == 60
    assert deal.name == "Big deal"
    assert deal.stage == "QUALIFICATION"
    assert deal.closed_by is None
    assert deal.contacts.count() == 1
    assert deal.teams.count() == 1
    assert deal.tags.count() == 1
    assert deal.assigned_to.count() == 1
    mail.assert_not_called()


def test_an_invalid_value_writes_nothing_and_returns_errors(request_obj, deal):
    errors = update_deal(
        request_obj, deal, {"stage": "CLOSED_WON", "closed_on": "2026-02-01"}
    )
    assert set(errors) == {"amount"}
    deal.refresh_from_db()
    assert deal.stage == "QUALIFICATION"
    assert deal.closed_on is None
    assert deal.closed_by is None


def test_closing_a_deal_records_who_closed_it(request_obj, deal, admin_profile):
    errors = update_deal(
        request_obj,
        deal,
        {"stage": "CLOSED_WON", "amount": "9000.00", "closed_on": "2026-02-01"},
    )
    assert errors is None
    deal.refresh_from_db()
    assert deal.stage == "CLOSED_WON"
    assert deal.closed_by == admin_profile


def test_assignees_replace_and_email_only_new_people(
    request_obj,
    deal,
    org_a,
    user_profile,
    other_profile,
    django_capture_on_commit_callbacks,
):
    deal.assigned_to.add(user_profile)
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_deal(
            request_obj,
            deal,
            {"assigned_to": [str(user_profile.id), str(other_profile.id)]},
        )
    assert errors is None
    assert set(deal.assigned_to.all()) == {user_profile, other_profile}
    mail.assert_called_once_with([other_profile.id], deal.id, str(org_a.id))


def test_another_orgs_assignee_is_ignored_or_refused(
    request_obj,
    deal,
    org_a,
    user_profile,
    profile_b,
    django_capture_on_commit_callbacks,
):
    """Ignored, as the PATCH does today: the write succeeds without them."""
    with patch(MAIL) as mail, django_capture_on_commit_callbacks(execute=True):
        errors = update_deal(
            request_obj,
            deal,
            {"assigned_to": [str(user_profile.id), str(profile_b.id)]},
        )
    assert errors is None
    assert list(deal.assigned_to.all()) == [user_profile]
    mail.assert_called_once_with([user_profile.id], deal.id, str(org_a.id))


def test_the_email_waits_for_the_commit(
    request_obj, deal, org_a, other_profile, django_capture_on_commit_callbacks
):
    with patch(MAIL) as mail:
        with django_capture_on_commit_callbacks() as callbacks:
            update_deal(request_obj, deal, {"assigned_to": [str(other_profile.id)]})
        mail.assert_not_called()
        for callback in callbacks:
            callback()
    mail.assert_called_once_with([other_profile.id], deal.id, str(org_a.id))
