"""Moving recurring-invoice schedules past periods that must not be billed,
and starting Invoices fresh when it comes back on.

``generate_recurring_invoices`` bills one period per run and then advances one
period, so a schedule left behind (beat not running, or Invoices switched off)
would bill every missed period, one a night, until it caught up.
"""

from datetime import date
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from common.org_time import org_timezone
from invoices.models import RecurringInvoice
from invoices.tasks import expiry_candidates, overdue_candidates


def advance_missed(
    org, today: date, *, include_today: bool = False, dry_run: bool = False
) -> list[tuple[UUID, date, date]]:
    """Move ``org``'s active schedules due before ``today`` (or on it, with
    ``include_today``) to their first period past that bound, billing nothing.

    Returns ``(pk, old date, new date)`` for each schedule moved. One whose
    ``end_date`` has passed is left for ``generate_recurring_invoices`` to
    deactivate.
    """

    def missed(day):
        return day <= today if include_today else day < today

    bound = "next_generation_date__lte" if include_today else "next_generation_date__lt"
    moved = []
    with transaction.atomic():
        templates = RecurringInvoice.objects.filter(
            org=org, is_active=True, **{bound: today}
        ).order_by("next_generation_date", "id")
        for recurring in templates:
            if recurring.end_date and recurring.end_date < today:
                continue
            old = recurring.next_generation_date
            while missed(recurring.next_generation_date):
                recurring.next_generation_date = recurring.calculate_next_date()
            new = recurring.next_generation_date
            if not dry_run:
                # One column, matched on the value just read, so a run racing
                # the task cannot move a schedule twice. update() skips save(),
                # so no audit stamps or signals fire.
                updated = RecurringInvoice.objects.filter(
                    pk=recurring.pk, org=org, next_generation_date=old
                ).update(next_generation_date=new)
                if not updated:
                    continue
            moved.append((recurring.pk, old, new))
    return moved


def start_fresh(org) -> None:
    """Invoices is back on: move every schedule to its next date after today,
    so nothing that fell due while it was off is billed later, and mark what
    fell overdue or expired meanwhile."""
    with org_timezone(org):
        today = timezone.localdate()
    advance_missed(org, today, include_today=True)
    # update(), not save(): a status catching up after the fact sends no
    # webhook, runs no rule and emails no one.
    now = timezone.now()
    overdue_candidates(org, today).update(status="Overdue", updated_at=now)
    expiry_candidates(org, today).update(status="Expired", updated_at=now)
