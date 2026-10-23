"""Move recurring-invoice templates past the periods missed while beat was off.

Run once, before the Celery beat scheduler is first started (or restarted after
a long outage). `generate_recurring_invoices` bills one period per template per
run and then advances by one period, so a template whose next generation date
is months in the past would bill every missed period, one a night, until it
caught up. This command skips those periods instead: each active template whose
next generation date is before today (in the org's timezone, as the task reads
it) is advanced with `RecurringInvoice.calculate_next_date` until it is on or
after today. A date equal to today is the current period and is left alone.

It creates no invoices, sends no email, and touches only `next_generation_date`.
A template whose `end_date` has passed is left as it is, so the task handles it
the way it always has (deactivated, not billed). Running it twice changes
nothing the second time.

Usage:
    python manage.py advance_missed_recurring_invoices --dry-run
    python manage.py advance_missed_recurring_invoices

Orgs are walked through the unscoped `organization` table with the RLS context
set per org, the same pattern as `common.tasks.purge_read_notifications`, so it
works under the non-superuser role production connects as.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from common.models import Org
from common.org_time import activate_org_timezone
from common.tasks import clear_rls_context, set_rls_context
from invoices.schedules import advance_missed


class Command(BaseCommand):
    help = (
        "Advance active recurring-invoice templates whose next generation date "
        "is in the past to their first current or future period, so a newly "
        "started beat does not bill the missed periods."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report per-org counts and change nothing.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        verb = "would be advanced" if dry_run else "advanced"
        total = 0
        try:
            for org in Org.objects.order_by("name", "id"):
                set_rls_context(org.id)
                activate_org_timezone(org)
                today = timezone.localdate()
                moved = advance_missed(org, today, dry_run=dry_run)
                if moved:
                    self.stdout.write(
                        f"Org {org.id} ({org.name}): {len(moved)} template(s) {verb}"
                    )
                    for pk, old, new in moved:
                        self.stdout.write(f"  {pk}: {old} -> {new}")
                total += len(moved)
        finally:
            timezone.deactivate()
            clear_rls_context()
        prefix = "DRY RUN, nothing changed. " if dry_run else ""
        self.stdout.write(f"{prefix}Total: {total} template(s) {verb}")
