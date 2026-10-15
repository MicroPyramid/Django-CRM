"""Account statements: what one account was billed and paid over a period.

A statement is computed from the invoices and payments on record, never
stored, so it cannot disagree with them. There are no exchange rates, so it is
one section per currency, each with:

* an opening balance: everything billed before the period, less everything
  paid and cancelled before it;
* the period's entries in date order, each with the running balance: an
  invoice on its issue date, a payment on its payment date, and a cancellation
  on the day it happened;
* a closing balance: the opening balance plus the period's entries.

Billed means the customer was asked to pay. Draft and Pending invoices were
not, so they are left off. A cancelled invoice stays on when it was sent or
paid toward: it is billed on its issue date and reversed on the day it was
cancelled, so a statement for an earlier month still closes on the balance it
showed then, and any payment it took leaves the account in credit. A cancelled
invoice nobody was sent or paid was never billed, and is left off.

Admin-only (see `api_views._statement_or_error`): it sums every invoice on the
account, including ones a member may not open.
"""

from decimal import Decimal

from django.db.models import Exists, F, OuterRef, Q, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from common.money import group_by_currency
from common.validators import date_param
from invoices.models import Invoice, Payment

# The longest period one statement covers, counting both ends: a year,
# leap year included. It bounds what one request may load and render.
MAX_STATEMENT_DAYS = 366

ZERO = Decimal("0")

# Within a day: what was billed, then what was paid, then what was cancelled.
_KIND_ORDER = {"invoice": 0, "payment": 1, "cancellation": 2}


def statement_period(params):
    """``(start, end)`` from a query string, or raise a ValidationError.

    Both dates are optional and default to this month so far, in the org's
    day (`timezone.localdate()` is the org's inside a request).
    """
    today = timezone.localdate()
    start = date_param(params, "start_date") or today.replace(day=1)
    end = date_param(params, "end_date") or today
    if end < start:
        raise ValidationError(
            {"end_date": ["The end date must be on or after the start date."]}
        )
    if (end - start).days + 1 > MAX_STATEMENT_DAYS:
        raise ValidationError(
            {"end_date": [f"A statement can cover at most {MAX_STATEMENT_DAYS} days."]}
        )
    return start, end


def billed_invoices(account):
    """The invoices on ``account`` its customer was asked to pay."""
    paid_toward = Exists(Payment.objects.filter(invoice=OuterRef("pk")))
    return (
        Invoice.objects.filter(org=account.org, account=account)
        .exclude(status__in=("Draft", "Pending"))
        .filter(~Q(status="Cancelled") | Q(sent_at__isnull=False) | Q(paid_toward))
    )


def _payment_description(payment):
    detail = payment.get_payment_method_display()
    if payment.reference_number:
        detail = f"{detail}, ref {payment.reference_number}"
    return f"Payment ({detail})"


def build_statement(account, start, end):
    """``account``'s statement from ``start`` to ``end``, both included.

    Amounts are signed: positive adds to what the account owes, negative takes
    from it. A currency with no opening balance and nothing in the period is
    left out.
    """
    invoices = billed_invoices(account)
    cancellations = invoices.filter(status="Cancelled").annotate(
        cancelled_on=Coalesce(TruncDate("cancelled_at"), "issue_date")
    )
    payments = Payment.objects.filter(org=account.org, invoice__in=invoices)

    before = {}
    group_by_currency(
        invoices.filter(issue_date__lt=start), before, invoiced=Sum("total_amount")
    )
    group_by_currency(
        cancellations.filter(cancelled_on__lt=start),
        before,
        cancelled=Sum("total_amount"),
    )
    group_by_currency(
        payments.filter(payment_date__lt=start),
        before,
        currency=F("invoice__currency"),
        paid=Sum("amount"),
    )

    # (sort key, currency, invoice, entry) for everything dated in the period.
    dated = [
        (
            (invoice.issue_date, _KIND_ORDER["invoice"], invoice.invoice_number),
            invoice.currency,
            invoice,
            {
                "date": invoice.issue_date,
                "kind": "invoice",
                "description": invoice.invoice_title,
                "amount": invoice.total_amount,
            },
        )
        for invoice in invoices.filter(issue_date__range=(start, end))
    ]
    dated += [
        (
            (invoice.cancelled_on, _KIND_ORDER["cancellation"], invoice.invoice_number),
            invoice.currency,
            invoice,
            {
                "date": invoice.cancelled_on,
                "kind": "cancellation",
                "description": "Invoice cancelled",
                "amount": -invoice.total_amount,
            },
        )
        for invoice in cancellations.filter(cancelled_on__range=(start, end))
    ]
    dated += [
        (
            (
                payment.payment_date,
                _KIND_ORDER["payment"],
                payment.invoice.invoice_number,
                payment.created_at,
            ),
            payment.invoice.currency,
            payment.invoice,
            {
                "date": payment.payment_date,
                "kind": "payment",
                "description": _payment_description(payment),
                "amount": -payment.amount,
            },
        )
        for payment in payments.filter(payment_date__range=(start, end)).select_related(
            "invoice"
        )
    ]
    dated.sort(key=lambda row: row[0])

    sections = []
    for code in sorted(set(before) | {row[1] for row in dated}):
        prior = before.get(code, {})
        opening = (
            (prior.get("invoiced") or ZERO)
            - (prior.get("paid") or ZERO)
            - (prior.get("cancelled") or ZERO)
        )
        entries = []
        totals = {"invoice": ZERO, "payment": ZERO, "cancellation": ZERO}
        balance = opening
        for _, currency, invoice, entry in dated:
            if currency != code:
                continue
            balance += entry["amount"]
            totals[entry["kind"]] += abs(entry["amount"])
            entries.append(
                {
                    **entry,
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "balance": balance,
                }
            )
        if not entries and not opening:
            continue
        sections.append(
            {
                "currency": code,
                "opening_balance": opening,
                "invoiced": totals["invoice"],
                "paid": totals["payment"],
                "cancelled": totals["cancellation"],
                "closing_balance": balance,
                "entries": entries,
            }
        )

    return {
        "account": {"id": account.id, "name": account.name},
        "start_date": start,
        "end_date": end,
        "currencies": sections,
    }
