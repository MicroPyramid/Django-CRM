"""The invoice jobs while Invoices is off, and once it is back on.

Every job skips an org with Invoices off, and every queued customer email
waits for nothing. Switching it back on starts fresh from that day: schedules
move past it, what fell overdue or expired meanwhile is marked silently, and
no schedule or reminder that fell due while it was off is sent later.
"""

import datetime
from unittest.mock import patch

import pytest
from django.core import mail
from django.db import connection
from django.utils import timezone

from automation.models import AutomationRun
from common.module_settings import change_modules
from common.testing import (
    clear_rls_context,
    restore_rls_context,
    rls_org,
    set_modules_off,
)
from invoices.models import (
    Estimate,
    Invoice,
    RecurringInvoice,
    RecurringInvoiceLineItem,
)
from invoices.tasks import (
    check_expired_estimates,
    check_overdue_invoices,
    generate_recurring_invoices,
    process_payment_reminders,
    send_estimate_to_client,
    send_invoice_to_client,
    send_payment_reminder,
)
from webhooks.models import WebhookDelivery, WebhookEndpoint

pytestmark = pytest.mark.django_db

DAY = datetime.timedelta(days=1)
WEEK = datetime.timedelta(weeks=1)


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


def _run(task):
    # Each job clears the RLS context on its way out; the test reads its own
    # rows afterwards.
    try:
        return task()
    finally:
        restore_rls_context()


def _schedule(org, next_date, *, lines=False, **extra):
    schedule = RecurringInvoice.objects.create(
        title="Hosting",
        frequency="WEEKLY",
        start_date=next_date,
        next_generation_date=next_date,
        is_active=True,
        org=org,
        **extra,
    )
    if lines:
        RecurringInvoiceLineItem.objects.create(
            recurring_invoice=schedule,
            org=org,
            name="Hosting",
            quantity="1",
            unit_price="50",
        )
    return schedule


def _invoice(org, due_date, **extra):
    fields = {
        "invoice_title": "Work",
        "status": "Sent",
        "currency": "USD",
        "client_email": "buyer@example.com",
        "due_date": due_date,
        "reminder_days_before": 0,
        "reminder_days_after": 0,
        **extra,
    }
    return Invoice.objects.create(org=org, **fields)


def _estimate(org, expiry_date, **extra):
    fields = {"title": "Quote", "status": "Sent", "currency": "USD", **extra}
    return Estimate.objects.create(org=org, expiry_date=expiry_date, **fields)


def _status(record):
    record.refresh_from_db()
    return record.status


def test_invoice_jobs_skip_an_org_with_invoices_off(org_a, org_b, admin_profile):
    _switch(org_a, admin_profile, "invoices")
    today = timezone.localdate()
    seeded = {}
    for org in (org_a, org_b):
        with rls_org(org):
            seeded[org.id] = (
                _schedule(org, today),
                _invoice(org, today - 10 * DAY, reminder_days_after=7),
                _estimate(org, today - 3 * DAY),
            )

    reminded = []
    with patch("invoices.tasks.send_payment_reminder.delay") as remind:
        remind.side_effect = lambda invoice_id, org_id, **kw: reminded.append(org_id)
        for task in (
            generate_recurring_invoices,
            check_overdue_invoices,
            process_payment_reminders,
            check_expired_estimates,
        ):
            _run(task)

    schedule, invoice, estimate = seeded[org_a.id]
    schedule.refresh_from_db()
    assert schedule.next_generation_date == today
    assert Invoice.objects.filter(org=org_a).count() == 1
    assert _status(invoice) == "Sent"
    assert _status(estimate) == "Sent"

    with rls_org(org_b):
        schedule, invoice, estimate = seeded[org_b.id]
        schedule.refresh_from_db()
        assert schedule.next_generation_date == today + WEEK
        assert Invoice.objects.filter(org=org_b).count() == 2
        assert _status(invoice) == "Overdue"
        assert _status(estimate) == "Expired"
    assert reminded == [str(org_b.id)]


def test_weekly_schedule_off_for_three_months_bills_nothing_missed(
    org_a, admin_profile, clock, django_capture_on_commit_callbacks
):
    today = timezone.localdate()
    _switch(org_a, admin_profile, "invoices")
    schedule = _schedule(
        org_a,
        today - 91 * DAY,
        lines=True,
        auto_send=True,
        client_email="buyer@example.com",
    )

    with (
        patch("invoices.tasks.send_invoice_to_client.delay") as send,
        django_capture_on_commit_callbacks(execute=True),
    ):
        _run(generate_recurring_invoices)
        assert not Invoice.objects.exists()

        _switch(org_a, admin_profile)
        schedule.refresh_from_db()
        assert schedule.next_generation_date == today + WEEK
        _run(generate_recurring_invoices)
        assert not Invoice.objects.exists()

        clock.advance(weeks=1)
        _run(generate_recurring_invoices)

    invoice = Invoice.objects.get()
    assert invoice.issue_date == today + WEEK
    assert send.call_count == 1
    schedule.refresh_from_db()
    assert schedule.invoices_generated == 1
    assert schedule.next_generation_date == today + 2 * WEEK


def test_a_schedule_due_on_the_switch_on_day_moves_too(org_a, admin_profile, clock):
    today = timezone.localdate()
    _switch(org_a, admin_profile, "invoices")
    schedule = _schedule(org_a, today)

    _switch(org_a, admin_profile)
    schedule.refresh_from_db()
    assert schedule.next_generation_date == today + WEEK
    _run(generate_recurring_invoices)
    assert not Invoice.objects.exists()


def test_switching_off_moves_no_schedule(org_a, admin_profile, clock):
    """Pin: only a switch-on moves a schedule."""
    today = timezone.localdate()
    past = _schedule(org_a, today - 20 * DAY)
    due_today = _schedule(org_a, today)

    _switch(org_a, admin_profile, "invoices")

    past.refresh_from_db()
    due_today.refresh_from_db()
    assert past.next_generation_date == today - 20 * DAY
    assert due_today.next_generation_date == today


def test_switch_on_marks_what_fell_overdue_or_expired_while_off_silently(
    admin_client, org_a, admin_profile, django_capture_on_commit_callbacks
):
    _switch(org_a, admin_profile, "invoices")
    WebhookEndpoint.objects.create(
        org=org_a,
        url="https://hooks.example.com/in",
        events=["invoice.updated"],
        created_by=admin_profile.user,
    )
    today = timezone.localdate()
    fell_due = _invoice(org_a, today - 5 * DAY)
    paid = _invoice(org_a, today - 5 * DAY, status="Paid")
    due_later = _invoice(org_a, today + 2 * DAY)
    lapsed = _estimate(org_a, today - 3 * DAY)
    expires_later = _estimate(org_a, today + DAY)

    with (
        patch("webhooks.emit.deliver_webhook.delay"),
        django_capture_on_commit_callbacks(execute=True),
    ):
        response = admin_client.put(
            "/api/org/modules/", {"off": [], "order": []}, format="json"
        )

    assert response.status_code == 200, response.content
    assert [_status(i) for i in (fell_due, paid, due_later)] == [
        "Overdue",
        "Paid",
        "Sent",
    ]
    assert [_status(e) for e in (lapsed, expires_later)] == ["Expired", "Sent"]
    assert not WebhookDelivery.objects.exists()
    # No automation adapter covers invoices or estimates today; this holds the
    # line if one is added.
    assert not AutomationRun.objects.exists()
    assert mail.outbox == []

    # The daily job's own change still reaches the endpoint, as it always has.
    with (
        patch("django.utils.timezone.now", return_value=timezone.now() + 3 * DAY),
        patch("webhooks.emit.deliver_webhook.delay"),
        django_capture_on_commit_callbacks(execute=True),
    ):
        _run(check_overdue_invoices)
    assert _status(due_later) == "Overdue"
    assert list(WebhookDelivery.objects.values_list("event", flat=True)) == [
        "invoice.updated"
    ]


def test_backdated_documents_created_after_switch_on_are_marked_by_the_next_run(
    org_a, admin_profile, clock
):
    _switch(org_a, admin_profile, "invoices")
    clock.advance(days=30)
    _switch(org_a, admin_profile)
    clock.advance(days=1)
    today = timezone.localdate()
    invoice = _invoice(org_a, today - 10 * DAY)
    estimate = _estimate(org_a, today - 10 * DAY)

    _run(check_overdue_invoices)
    _run(check_expired_estimates)

    assert (_status(invoice), _status(estimate)) == ("Overdue", "Expired")


def test_an_org_never_switched_off_is_marked_as_before(org_a):
    """Pin: with no switch-on stamp the status jobs work as they always have."""
    today = timezone.localdate()
    invoice = _invoice(org_a, today - DAY)
    estimate = _estimate(org_a, today - DAY)

    _run(check_overdue_invoices)
    _run(check_expired_estimates)

    assert org_a.modules_on_at == {}
    assert (_status(invoice), _status(estimate)) == ("Overdue", "Expired")


def test_reminders_skip_the_off_period_and_keep_their_cadence(
    org_a, admin_profile, clock
):
    _switch(org_a, admin_profile, "invoices")
    clock.advance(days=30)
    today = timezone.localdate()
    weekly = _invoice(
        org_a,
        today - 30 * DAY,
        reminder_frequency="WEEKLY",
        reminder_days_after=7,
        last_reminder_sent=timezone.now() - 20 * DAY,
    )
    once = _invoice(
        org_a, today - 10 * DAY, reminder_frequency="ONCE", reminder_days_after=7
    )
    upcoming = _invoice(
        org_a, today + 10 * DAY, reminder_frequency="ONCE", reminder_days_before=3
    )
    names = {str(weekly.id): "weekly", str(once.id): "once", str(upcoming.id): "up"}
    _switch(org_a, admin_profile)
    switched_on = clock.now

    def reminded_on(days_after_switch_on):
        clock.now = switched_on + days_after_switch_on * DAY
        sent = []

        def send_now(invoice_id, org_id, **kwargs):
            sent.append(names[invoice_id])
            send_payment_reminder(invoice_id, org_id)

        with patch("invoices.tasks.send_payment_reminder.delay", side_effect=send_now):
            _run(process_payment_reminders)
        return sent

    # Weekly from 20 days ago: due 13 and 6 days ago while off, then tomorrow.
    assert reminded_on(0) == []
    assert reminded_on(1) == ["weekly"]
    assert reminded_on(6) == []
    assert reminded_on(7) == ["up"]
    assert reminded_on(8) == ["weekly"]
    assert reminded_on(40) == ["weekly"]
    assert len(mail.outbox) == 4


def _sent_only_once_back_on(org, actor, send, state):
    """Run a queued customer email with Invoices off, then on again. While off
    it sends nothing and ``state()`` does not move."""
    before = state()
    _switch(org, actor, "invoices")
    send()
    assert (mail.outbox, state()) == ([], before)
    _switch(org, actor)
    send()
    assert len(mail.outbox) == 1


def test_a_queued_invoice_email_is_not_sent_while_invoices_is_off(org_a, admin_profile):
    invoice = _invoice(org_a, timezone.localdate() + 10 * DAY, status="Draft")

    _sent_only_once_back_on(
        org_a,
        admin_profile,
        lambda: send_invoice_to_client(
            str(invoice.id), str(org_a.id), include_pdf=False
        ),
        lambda: _status(invoice),
    )
    assert _status(invoice) == "Sent"


def test_a_queued_payment_reminder_is_not_sent_while_invoices_is_off(
    org_a, admin_profile
):
    invoice = _invoice(org_a, timezone.localdate() + 2 * DAY)

    def reminders():
        invoice.refresh_from_db()
        return invoice.reminder_count

    _sent_only_once_back_on(
        org_a,
        admin_profile,
        lambda: send_payment_reminder(str(invoice.id), str(org_a.id)),
        reminders,
    )
    assert reminders() == 1


def test_a_queued_estimate_email_is_not_sent_while_invoices_is_off(
    org_a, admin_profile
):
    estimate = _estimate(
        org_a,
        timezone.localdate() + 30 * DAY,
        status="Draft",
        client_email="buyer@example.com",
    )

    _sent_only_once_back_on(
        org_a,
        admin_profile,
        lambda: send_estimate_to_client(
            str(estimate.id), str(org_a.id), include_pdf=False
        ),
        lambda: _status(estimate),
    )
    assert _status(estimate) == "Sent"


@pytest.mark.postgres_only
def test_start_fresh_moves_schedules_under_rls(admin_client, org_a, org_b):
    """Skipped on SQLite. Under a non-superuser role an empty context matches no
    rows, so a moved schedule and a marked invoice prove the switch-on ran under
    its org's context, and org B's untouched ones that it stayed there."""
    if connection.vendor != "postgresql":
        pytest.skip("RLS requires PostgreSQL")
    past = timezone.localdate() - 20 * DAY
    ours = _schedule(org_a, past)
    our_invoice = _invoice(org_a, past)
    with rls_org(org_b):
        theirs = _schedule(org_b, past)
        their_invoice = _invoice(org_b, past)
    set_modules_off(org_a, "invoices")
    set_modules_off(org_b, "invoices")
    clear_rls_context()

    response = admin_client.put(
        "/api/org/modules/", {"off": [], "order": []}, format="json"
    )

    assert response.status_code == 200, response.content
    with rls_org(org_a):
        ours.refresh_from_db()
        assert ours.next_generation_date == past + 3 * WEEK
        assert _status(our_invoice) == "Overdue"
    with rls_org(org_b):
        theirs.refresh_from_db()
        assert theirs.next_generation_date == past
        assert _status(their_invoice) == "Sent"
