"""SLA escalation and stale timers while their module is off, and once it is
back on.

A breach whose deadline passed while Tickets was off never escalates or
reassigns, a timer that went stale while Timesheet was off is left running for
its owner to stop, and a customer email queued before Tickets went off is not
sent while it is off.
"""

import datetime
from unittest.mock import patch

import pytest
from django.core import mail
from django.utils import timezone

from cases.models import Case, CsatSurvey, EscalationPolicy, TimeEntry
from cases.tasks import (
    auto_stop_stale_timers,
    notify_portal_contacts,
    scan_for_breached_cases,
    send_csat_survey,
)
from common.models import Activity, Profile, User
from common.module_settings import change_modules
from common.testing import restore_rls_context, rls_org
from contacts.models import Contact

pytestmark = pytest.mark.django_db

HOUR = datetime.timedelta(hours=1)


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


@pytest.fixture(autouse=True)
def no_email():
    with patch("cases.tasks.send_email_to_assigned_user") as send:
        yield send


def _switch(org, actor, *off):
    """Leave exactly ``off`` switched off, through the one writer."""
    assert change_modules(org, actor, {"off": list(off), "order": []}) == {}
    org.refresh_from_db()


def _run(task, *args, **kwargs):
    # Each job clears the RLS context on its way out; the test reads its own
    # rows afterwards.
    try:
        return task(*args, **kwargs)
    finally:
        restore_rls_context()


def _agent(org, email):
    user = User.objects.create_user(email=email, password="x")
    return Profile.objects.create(user=user, org=org, role="USER", is_active=True)


def _policy(org, target):
    return EscalationPolicy.objects.create(
        org=org,
        priority="Urgent",
        first_response_action="notify_and_reassign",
        resolution_action="notify_and_reassign",
        first_response_target=target,
        resolution_target=target,
        is_active=True,
    )


def _case(org, created_at, *, first_response_hours=1, assignee=None):
    case = Case.objects.create(
        name="Printer on fire",
        status="New",
        priority="Urgent",
        sla_first_response_hours=first_response_hours,
        sla_resolution_hours=48,
        org=org,
    )
    Case.objects.filter(pk=case.pk).update(created_at=created_at)
    if assignee is not None:
        case.assigned_to.add(assignee)
    return case


def _timer(org, profile, started_at):
    case = Case.objects.create(name="Timed", status="New", org=org)
    return TimeEntry.objects.create(
        org=org, case=case, profile=profile, started_at=started_at
    )


def test_sla_scan_skips_an_org_with_tickets_off(org_a, org_b, admin_profile):
    _switch(org_a, admin_profile, "tickets")
    cases = {}
    for org in (org_a, org_b):
        with rls_org(org):
            _policy(org, _agent(org, f"agent-{org.id}@test.com"))
            cases[org.id] = _case(org, timezone.now() - 5 * HOUR)

    assert _run(scan_for_breached_cases) == 1

    cases[org_a.id].refresh_from_db()
    assert cases[org_a.id].escalation_count == 0
    with rls_org(org_b):
        cases[org_b.id].refresh_from_db()
        assert cases[org_b.id].escalation_count == 1


def test_breaches_from_the_off_period_never_escalate(
    org_a, admin_profile, clock, no_email
):
    _switch(org_a, admin_profile, "tickets")
    clock.advance(days=2)
    switched_on = clock.now
    target = _agent(org_a, "agent@test.com")
    _policy(org_a, target)
    missed_while_off = _case(org_a, switched_on - 3 * HOUR, assignee=admin_profile)
    due_after = _case(org_a, switched_on, assignee=admin_profile)
    _switch(org_a, admin_profile)

    assert _run(scan_for_breached_cases) == 0

    clock.advance(hours=1, minutes=5)
    assert _run(scan_for_breached_cases) == 1

    missed_while_off.refresh_from_db()
    due_after.refresh_from_db()
    assert missed_while_off.escalation_count == 0
    assert list(missed_while_off.assigned_to.all()) == [admin_profile]
    assert not Activity.objects.filter(
        action="ESCALATED", entity_id=missed_while_off.pk
    ).exists()
    assert due_after.escalation_count == 1
    assert list(due_after.assigned_to.all()) == [target]
    assert no_email.delay.call_count == 1


def test_stale_timers_skip_an_org_with_timesheet_off(
    org_a, org_b, admin_profile, profile_b
):
    _switch(org_a, admin_profile, "timesheet")
    long_ago = timezone.now() - 15 * HOUR
    ours = _timer(org_a, admin_profile, long_ago)
    with rls_org(org_b):
        theirs = _timer(org_b, profile_b, long_ago)

    assert _run(auto_stop_stale_timers, threshold_hours=12) == 1

    ours.refresh_from_db()
    assert ours.ended_at is None
    with rls_org(org_b):
        theirs.refresh_from_db()
        assert theirs.auto_stopped is True


def test_a_timer_that_went_stale_while_off_is_left_running(org_a, admin_profile, clock):
    _switch(org_a, admin_profile, "timesheet")
    clock.advance(days=1)
    entry = _timer(org_a, admin_profile, clock.now - 20 * HOUR)
    _switch(org_a, admin_profile)

    assert _run(auto_stop_stale_timers, threshold_hours=12) == 0
    clock.advance(hours=13)
    assert _run(auto_stop_stale_timers, threshold_hours=12) == 0

    entry.refresh_from_db()
    assert (entry.ended_at, entry.auto_stopped) == (None, False)


def test_a_timer_started_after_switch_on_is_stopped_as_before(
    org_a, admin_profile, clock
):
    """Pin: both were stopped before this change too. It holds the bound: the
    timer started two hours before the switch-on went stale after it."""
    _switch(org_a, admin_profile, "timesheet")
    clock.advance(days=1)
    started_before = _timer(org_a, admin_profile, clock.now - 2 * HOUR)
    _switch(org_a, admin_profile)
    clock.advance(minutes=1)
    started_after = _timer(org_a, _agent(org_a, "second@test.com"), clock.now)

    clock.advance(hours=13)
    assert _run(auto_stop_stale_timers, threshold_hours=12) == 2

    for entry in (started_before, started_after):
        entry.refresh_from_db()
        assert entry.auto_stopped is True


def _customer_case(org, status):
    case = Case.objects.create(
        org=org,
        name="Login bug",
        status=status,
        priority="Normal",
        resolved_at=timezone.now() if status == "Closed" else None,
    )
    case.contacts.add(
        Contact.objects.create(
            org=org, first_name="Pat", last_name="Smith", email="pat@example.com"
        )
    )
    return case


def test_a_queued_csat_survey_is_not_sent_while_tickets_is_off(org_a, admin_profile):
    case = _customer_case(org_a, "Closed")
    _switch(org_a, admin_profile, "tickets")
    mail.outbox.clear()

    assert send_csat_survey(str(case.id), str(org_a.id)) is None
    assert (mail.outbox, CsatSurvey.objects.count()) == ([], 0)

    _switch(org_a, admin_profile)
    assert send_csat_survey(str(case.id), str(org_a.id)) is not None
    assert (len(mail.outbox), CsatSurvey.objects.count()) == (1, 1)


def test_a_queued_portal_notice_is_not_sent_while_tickets_is_off(org_a, admin_profile):
    case = _customer_case(org_a, "New")
    _switch(org_a, admin_profile, "tickets")
    mail.outbox.clear()

    assert notify_portal_contacts(str(case.id), str(org_a.id), "status") == 0
    assert mail.outbox == []

    _switch(org_a, admin_profile)
    assert notify_portal_contacts(str(case.id), str(org_a.id), "status") == 1
    assert [m.to for m in mail.outbox] == [["pat@example.com"]]
