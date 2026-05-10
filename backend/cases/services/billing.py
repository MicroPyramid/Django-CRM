"""Helpers that turn billable :class:`cases.models.TimeEntry` rows into
draft :class:`invoices.models.InvoiceLineItem` shapes.

Kept in ``cases/services/`` so the cross-app glue lives on the cases side
of the boundary — the invoices app only consumes these dicts. Reach over
to ``invoices/api_views.py`` :class:`InvoiceFromTimeEntriesView` for the
actual endpoint that calls this helper.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable, List, Tuple


class TimeEntryInvoicingError(ValueError):
    """Raised when a set of time entries cannot be converted into invoice lines."""


def build_invoice_lines_from_entries(entries) -> Tuple[str, List[dict]]:
    """Validate ``entries`` and return ``(currency, lines)``.

    Each line is a dict suitable for ``InvoiceLineItem.objects.create(...)``
    keyword arguments (sans ``invoice``/``org`` which the caller injects).

    Rejects (raising :class:`TimeEntryInvoicingError`):

    * Empty input.
    * Mixed currencies — single invoices stay single-currency.
    * Already-invoiced entries.
    * Unstopped (running) entries.
    * Non-billable entries.
    """
    entries = list(entries)
    if not entries:
        raise TimeEntryInvoicingError("No time entries supplied.")

    currencies = {e.currency for e in entries}
    if len(currencies) > 1:
        raise TimeEntryInvoicingError(
            "Cannot invoice entries in multiple currencies: "
            f"{sorted(currencies)}."
        )
    currency = next(iter(currencies))

    for entry in entries:
        if entry.invoice_id is not None:
            raise TimeEntryInvoicingError(
                f"Time entry {entry.id} has already been invoiced."
            )
        if entry.ended_at is None:
            raise TimeEntryInvoicingError(
                f"Time entry {entry.id} is still running and cannot be invoiced."
            )
        if not entry.billable:
            raise TimeEntryInvoicingError(
                f"Time entry {entry.id} is not marked billable."
            )

    lines: List[dict] = []
    for index, entry in enumerate(entries):
        # Convert minutes → hours with two-decimal precision; quantity is the
        # billed quantity on the invoice line and Decimal works naturally with
        # the Invoice model's DecimalField columns.
        hours = (Decimal(entry.duration_minutes) / Decimal(60)).quantize(
            Decimal("0.01")
        )
        rate = entry.hourly_rate if entry.hourly_rate is not None else Decimal("0")
        case_name = entry.case.name if getattr(entry, "case", None) else "Time entry"
        body = entry.description.strip() if entry.description else ""
        full = f"{case_name} — {body}" if body else case_name
        lines.append(
            {
                "name": full[:255],
                "description": full[:500],
                "quantity": hours,
                "unit_price": rate,
                "order": index,
            }
        )
    return currency, lines


def attach_entries_to_invoice(entries: Iterable, invoice) -> int:
    """Set ``invoice`` on each entry. Returns the count updated."""
    from cases.models import TimeEntry

    ids = [e.id for e in entries]
    return TimeEntry.objects.filter(id__in=ids).update(invoice=invoice)
