"""One record of each registry object, for tests that sweep every object."""

import uuid

from django.utils import timezone

from accounts.models import Account
from cases.models import Case
from contacts.models import Contact
from invoices.models import Estimate, Invoice, RecurringInvoice
from leads.models import Lead
from opportunity.models import Opportunity
from tasks.models import Task


def _recurring_invoice(org):
    today = timezone.localdate()
    return RecurringInvoice.objects.create(
        title="Rec",
        frequency="MONTHLY",
        start_date=today,
        next_generation_date=today,
        org=org,
    )


_BUILDERS = {
    "lead": lambda org: Lead.objects.create(title="Rec", org=org),
    "contact": lambda org: Contact.objects.create(
        first_name="Rec", last_name="Person", org=org
    ),
    # Account names are unique per org, and tests make two in one org.
    "account": lambda org: Account.objects.create(
        name=f"Rec {uuid.uuid4().hex[:8]}", org=org
    ),
    "deal": lambda org: Opportunity.objects.create(
        name="Rec", stage="QUALIFICATION", org=org
    ),
    "ticket": lambda org: Case.objects.create(name="Rec", status="New", org=org),
    "task": lambda org: Task.objects.create(
        title="Rec", status="New", priority="Low", org=org
    ),
    "invoice": lambda org: Invoice.objects.create(invoice_title="Rec", org=org),
    "estimate": lambda org: Estimate.objects.create(title="Rec", org=org),
    "recurring_invoice": _recurring_invoice,
}


def make_record(key, org, created_by=None):
    """Create a record of `key` in `org`; unknown keys raise KeyError.

    `created_by` is set with a queryset update because `BaseModel.save()`
    overwrites it from the request user, which is None outside a request.
    """
    record = _BUILDERS[key](org)
    type(record).objects.filter(pk=record.pk).update(created_by=created_by)
    record.refresh_from_db()
    return record
