"""Deleting a payment moves the invoice's status back with its balance.

`Payment.update_invoice_payment` only moved the status forward, so an invoice
that went Paid or Partially_Paid stayed that way, with `paid_at` set, after
the payment that earned it was deleted.
"""

import datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from invoices.models import Invoice, Payment


def _invoice(org, **extra):
    invoice = Invoice.objects.create(
        org=org, invoice_title="Work", client_email="a@b.co", status="Sent", **extra
    )
    Invoice.objects.filter(pk=invoice.pk).update(
        total_amount=Decimal("100.00"), amount_due=Decimal("100.00")
    )
    invoice.refresh_from_db()
    return invoice


def _pay(invoice, amount):
    return Payment.objects.create(
        invoice=invoice,
        org=invoice.org,
        amount=Decimal(amount),
        payment_date=timezone.localdate(),
    )


@pytest.mark.django_db
class TestPaymentDeleteStatus:
    def test_deleting_the_only_payment_reopens_a_paid_invoice(self, org_a):
        invoice = _invoice(org_a)
        payment = _pay(invoice, "100.00")
        invoice.refresh_from_db()
        assert invoice.status == "Paid" and invoice.paid_at

        payment.delete()

        invoice.refresh_from_db()
        assert invoice.status == "Sent"
        assert invoice.paid_at is None
        assert invoice.amount_due == Decimal("100.00")

    def test_deleting_one_of_two_payments_leaves_it_partially_paid(self, org_a):
        invoice = _invoice(org_a)
        first = _pay(invoice, "60.00")
        _pay(invoice, "40.00")

        first.delete()

        invoice.refresh_from_db()
        assert invoice.status == "Partially_Paid"
        assert invoice.paid_at is None
        assert invoice.amount_due == Decimal("60.00")

    def test_deleting_the_last_partial_payment_reopens_it(self, org_a):
        invoice = _invoice(org_a)
        payment = _pay(invoice, "30.00")

        payment.delete()

        invoice.refresh_from_db()
        assert invoice.status == "Sent"

    def test_reopened_invoice_past_due_is_overdue(self, org_a):
        invoice = _invoice(
            org_a, due_date=timezone.localdate() - datetime.timedelta(days=3)
        )
        payment = _pay(invoice, "100.00")

        payment.delete()

        invoice.refresh_from_db()
        assert invoice.status == "Overdue"

    def test_reopened_viewed_invoice_is_viewed(self, org_a):
        invoice = _invoice(org_a, viewed_at=timezone.now())
        payment = _pay(invoice, "100.00")

        payment.delete()

        invoice.refresh_from_db()
        assert invoice.status == "Viewed"
