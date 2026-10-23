"""The deal and goal jobs while their module is off, and once it is back on.

A deal that went stale while Pipeline was off is never alerted, and a goal
milestone reached while Goals was off is settled silently at switch-on.
"""

import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core import mail
from django.utils import timezone

from common.module_settings import change_modules
from common.testing import restore_rls_context, rls_org
from opportunity.models import Opportunity, SalesGoal
from opportunity.tasks import check_goal_milestones as _check_goal_milestones
from opportunity.tasks import check_stale_opportunities as _check_stale_opportunities

pytestmark = pytest.mark.django_db

DAY = datetime.timedelta(days=1)


class Clock:
    def __init__(self):
        self.now = datetime.datetime(2026, 10, 14, 12, 0, tzinfo=datetime.UTC)

    def advance(self, **delta):
        self.now += datetime.timedelta(**delta)


@pytest.fixture
def clock():
    c = Clock()
    with patch("django.utils.timezone.now", side_effect=lambda: c.now):
        yield c


def _switch(org, actor, *off):
    """Leave exactly ``off`` switched off, through the one writer."""
    assert change_modules(org, actor, {"off": list(off), "order": []}) == {}
    org.refresh_from_db()


# Each job leaves the last org's RLS context set; the test reads its own rows
# afterwards.
def check_stale_opportunities():
    try:
        _check_stale_opportunities()
    finally:
        restore_rls_context()


def check_goal_milestones():
    try:
        _check_goal_milestones()
    finally:
        restore_rls_context()


def _deal(org, user, name, days_in_stage):
    # Prospecting expects 14 days, so a deal is red after 21.
    return Opportunity.objects.create(
        name=name,
        stage="PROSPECTING",
        org=org,
        created_by=user,
        stage_changed_at=timezone.now() - days_in_stage * DAY,
    )


def _alerted(mock_alert):
    return [
        (call.args[0].id, sorted(opp.name for opp, *_ in call.args[1]))
        for call in mock_alert.call_args_list
    ]


def _goal(org, profile):
    today = timezone.localdate()
    return SalesGoal.objects.create(
        name="Quarter",
        goal_type="REVENUE",
        target_value=Decimal("100"),
        period_type="MONTHLY",
        period_start=today - 5 * DAY,
        period_end=today + 25 * DAY,
        assigned_to=profile,
        org=org,
    )


def _won(org, user, profile, amount):
    deal = Opportunity.objects.create(
        name=f"Won {amount}",
        stage="CLOSED_WON",
        amount=Decimal(amount),
        closed_on=timezone.localdate(),
        org=org,
        created_by=user,
    )
    deal.assigned_to.add(profile)


@patch("opportunity.tasks.send_stale_deals_alert")
def test_stale_deal_alert_skips_an_org_with_deals_off(
    mock_alert, org_a, org_b, admin_user, admin_profile, user_b
):
    _switch(org_a, admin_profile, "deals")
    _deal(org_a, admin_user, "Ours", 30)
    with rls_org(org_b):
        _deal(org_b, user_b, "Theirs", 30)

    check_stale_opportunities()

    assert _alerted(mock_alert) == [(org_b.id, ["Theirs"])]


@patch("opportunity.tasks.send_stale_deals_alert")
def test_deals_that_went_stale_while_off_are_not_alerted(
    mock_alert, org_a, admin_user, admin_profile, clock
):
    _switch(org_a, admin_profile, "deals")
    clock.advance(days=30)
    _deal(org_a, admin_user, "Went stale while off", 30)
    _deal(org_a, admin_user, "Turns stale later", 15)
    _switch(org_a, admin_profile)

    check_stale_opportunities()
    assert _alerted(mock_alert) == []

    clock.advance(days=7)
    check_stale_opportunities()
    assert _alerted(mock_alert) == [(org_a.id, ["Turns stale later"])]


def test_goal_milestones_skip_an_org_with_goals_off(
    org_a, org_b, admin_user, admin_profile, user_b, profile_b
):
    _switch(org_a, admin_profile, "goals")
    ours = _goal(org_a, admin_profile)
    _won(org_a, admin_user, admin_profile, "60")
    with rls_org(org_b):
        theirs = _goal(org_b, profile_b)
        _won(org_b, user_b, profile_b, "60")

    check_goal_milestones()

    ours.refresh_from_db()
    assert ours.milestone_50_notified is False
    with rls_org(org_b):
        theirs.refresh_from_db()
        assert theirs.milestone_50_notified is True
    assert [m.to for m in mail.outbox] == [[user_b.email]]


def test_milestones_reached_while_off_send_nothing_after_switch_on(
    org_a, admin_user, admin_profile
):
    _switch(org_a, admin_profile, "goals")
    goal = _goal(org_a, admin_profile)
    _won(org_a, admin_user, admin_profile, "60")
    check_goal_milestones()
    goal.refresh_from_db()
    assert goal.milestone_50_notified is False

    _switch(org_a, admin_profile)
    goal.refresh_from_db()
    assert (goal.milestone_50_notified, goal.milestone_90_notified) == (True, False)
    check_goal_milestones()
    assert mail.outbox == []

    _won(org_a, admin_user, admin_profile, "35")
    check_goal_milestones()
    assert [m.subject for m in mail.outbox] == [
        "[BottleCRM] Goal 'Quarter' reached 90%!"
    ]


def test_switching_pipeline_back_on_settles_goals_too(org_a, admin_user, admin_profile):
    """Goals needs Pipeline, so it comes back with it and starts fresh then."""
    _switch(org_a, admin_profile, "deals")
    goal = _goal(org_a, admin_profile)
    _won(org_a, admin_user, admin_profile, "60")

    _switch(org_a, admin_profile)
    goal.refresh_from_db()
    assert goal.milestone_50_notified is True
    check_goal_milestones()
    assert mail.outbox == []
