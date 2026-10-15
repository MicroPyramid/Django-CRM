"""Account statements: what one account was billed and paid over a period (#810).

`GET /api/invoices/statements/<account>/` and its `pdf/` twin. Per currency, a
statement has an opening balance, the period's invoices, payments and
cancellations in date order with a running balance, and a closing balance.

Admin-only, like the invoice reports: it sums every invoice on the account,
including ones a member may not open, and a statement built from only the
invoices a member can see would show the customer a wrong balance.
"""

import datetime
import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

from accounts.models import Account
from invoices.models import Invoice, Payment

pytestmark = pytest.mark.django_db

OCTOBER = "start_date=2026-10-01&end_date=2026-10-31"
SEPTEMBER = "start_date=2026-09-01&end_date=2026-09-30"


def _url(account_id, query=OCTOBER, pdf=False):
    return f"/api/invoices/statements/{account_id}/{'pdf/' if pdf else ''}?{query}"


def _invoice(account, total, issued, status="Sent", currency="USD", **fields):
    """An invoice for ``total``, stored as the lifecycle endpoints leave one."""
    invoice = Invoice.objects.create(
        invoice_title=fields.pop("title", "Work"),
        account=account,
        currency=currency,
        issue_date=issued,
        org=account.org,
    )
    Invoice.objects.filter(pk=invoice.pk).update(
        status=status,
        total_amount=Decimal(total),
        amount_due=Decimal(total),
        **fields,
    )
    invoice.refresh_from_db()
    return invoice


def _pay(invoice, amount, on):
    return Payment.objects.create(
        invoice=invoice,
        amount=Decimal(amount),
        payment_date=on,
        payment_method="BANK_TRANSFER",
        org=invoice.org,
    )


def _noon(day):
    return datetime.datetime.combine(day, datetime.time(12), tzinfo=datetime.UTC)


def _sections(response):
    assert response.status_code == 200, response.content
    return {s["currency"]: s for s in response.json()["currencies"]}


def _rows(section):
    return [
        (e["date"], e["kind"], e["amount"], e["balance"]) for e in section["entries"]
    ]


@pytest.fixture
def account(org_a):
    return Account.objects.create(name="Acme", org=org_a)


class TestWhoMayRead:
    @pytest.mark.parametrize("pdf", [False, True], ids=["json", "pdf"])
    def test_a_member_is_refused(self, user_client, account, pdf):
        _invoice(account, "100.00", datetime.date(2026, 10, 2))
        response = user_client.get(_url(account.id, pdf=pdf))
        assert response.status_code == 403
        assert "currencies" not in response.json()

    def test_a_member_learns_nothing_about_which_accounts_exist(self, user_client):
        response = user_client.get(_url(uuid.uuid4()))
        assert response.status_code == 403

    def test_an_admin_may_read_it(self, admin_client, account):
        assert admin_client.get(_url(account.id)).status_code == 200

    def test_another_orgs_account_is_not_found(self, admin_client, org_b):
        theirs = Account.objects.create(name="Theirs", org=org_b)
        for pdf in (False, True):
            assert admin_client.get(_url(theirs.id, pdf=pdf)).status_code == 404

    def test_an_unknown_account_is_not_found(self, admin_client):
        assert admin_client.get(_url(uuid.uuid4())).status_code == 404

    def test_signed_out_is_refused(self, unauthenticated_client, account):
        response = unauthenticated_client.get(_url(account.id))
        assert response.status_code in (401, 403)
        assert "currencies" not in response.json()


class TestBalances:
    def test_opening_balance_entries_and_closing_balance(self, admin_client, account):
        earlier = _invoice(account, "100.00", datetime.date(2026, 9, 10))
        _pay(earlier, "40.00", datetime.date(2026, 9, 20))
        october = _invoice(account, "250.00", datetime.date(2026, 10, 5), title="Build")
        _pay(earlier, "60.00", datetime.date(2026, 10, 12))
        _pay(october, "100.00", datetime.date(2026, 10, 20))
        _invoice(account, "30.00", datetime.date(2026, 11, 2))  # after the period

        response = admin_client.get(_url(account.id))
        usd = _sections(response)["USD"]

        body = response.json()
        assert body["account"] == {"id": str(account.id), "name": "Acme"}
        assert (body["start_date"], body["end_date"]) == ("2026-10-01", "2026-10-31")
        assert usd["opening_balance"] == "60.00"
        assert _rows(usd) == [
            ("2026-10-05", "invoice", "250.00", "310.00"),
            ("2026-10-12", "payment", "-60.00", "250.00"),
            ("2026-10-20", "payment", "-100.00", "150.00"),
        ]
        assert (usd["invoiced"], usd["paid"], usd["cancelled"]) == (
            "250.00",
            "160.00",
            "0.00",
        )
        assert usd["closing_balance"] == "150.00"

    def test_entries_say_what_they_are(self, admin_client, account):
        invoice = _invoice(account, "250.00", datetime.date(2026, 10, 5), title="Build")
        payment = _pay(invoice, "100.00", datetime.date(2026, 10, 20))
        Payment.objects.filter(pk=payment.pk).update(reference_number="TX-9")

        entries = _sections(admin_client.get(_url(account.id)))["USD"]["entries"]

        assert [(e["invoice_id"], e["invoice_number"]) for e in entries] == [
            (str(invoice.id), invoice.invoice_number)
        ] * 2
        assert [e["description"] for e in entries] == [
            "Build",
            "Payment (Bank Transfer, ref TX-9)",
        ]

    def test_drafts_and_pending_invoices_were_never_billed(self, admin_client, account):
        _invoice(account, "500.00", datetime.date(2026, 10, 7), status="Draft")
        _invoice(account, "70.00", datetime.date(2026, 9, 7), status="Pending")
        assert _sections(admin_client.get(_url(account.id))) == {}

    def test_other_accounts_are_left_off(self, admin_client, account, org_a):
        other = Account.objects.create(name="Other", org=org_a)
        _invoice(other, "90.00", datetime.date(2026, 10, 3))
        assert _sections(admin_client.get(_url(account.id))) == {}

    def test_currencies_are_never_added_together(self, admin_client, account):
        _invoice(account, "100.00", datetime.date(2026, 10, 3))
        _invoice(account, "80.00", datetime.date(2026, 10, 4), currency="EUR")
        sections = _sections(admin_client.get(_url(account.id)))
        assert sorted(sections) == ["EUR", "USD"]
        assert sections["USD"]["closing_balance"] == "100.00"
        assert sections["EUR"]["closing_balance"] == "80.00"

    def test_a_currency_is_shown_while_it_has_a_balance(self, admin_client, account):
        settled = _invoice(account, "80.00", datetime.date(2026, 9, 4), currency="EUR")
        _pay(settled, "80.00", datetime.date(2026, 9, 9))
        _invoice(account, "50.00", datetime.date(2026, 9, 6), currency="GBP")

        sections = _sections(admin_client.get(_url(account.id)))

        # EUR was settled before October and nothing happened in it since.
        assert sorted(sections) == ["GBP"]
        gbp = sections["GBP"]
        assert (gbp["opening_balance"], gbp["closing_balance"]) == ("50.00", "50.00")
        assert gbp["entries"] == []


class TestCancelledInvoices:
    def test_a_sent_invoice_is_reversed_on_the_day_it_was_cancelled(
        self, admin_client, account
    ):
        _invoice(
            account,
            "100.00",
            datetime.date(2026, 9, 15),
            status="Cancelled",
            sent_at=_noon(datetime.date(2026, 9, 15)),
            cancelled_at=_noon(datetime.date(2026, 10, 10)),
        )

        september = _sections(admin_client.get(_url(account.id, SEPTEMBER)))["USD"]
        october = _sections(admin_client.get(_url(account.id)))["USD"]

        # September still closes on what it showed the customer at the time.
        assert _rows(september) == [("2026-09-15", "invoice", "100.00", "100.00")]
        assert october["opening_balance"] == september["closing_balance"]
        assert _rows(october) == [("2026-10-10", "cancellation", "-100.00", "0.00")]
        assert october["entries"][0]["description"] == "Invoice cancelled"
        assert october["cancelled"] == "100.00"

    def test_cancelling_after_a_part_payment_leaves_the_account_in_credit(
        self, admin_client, account
    ):
        invoice = _invoice(account, "100.00", datetime.date(2026, 10, 2))
        _pay(invoice, "40.00", datetime.date(2026, 10, 4))
        Invoice.objects.filter(pk=invoice.pk).update(
            status="Cancelled", cancelled_at=_noon(datetime.date(2026, 10, 8))
        )

        usd = _sections(admin_client.get(_url(account.id)))["USD"]

        assert _rows(usd) == [
            ("2026-10-02", "invoice", "100.00", "100.00"),
            ("2026-10-04", "payment", "-40.00", "60.00"),
            ("2026-10-08", "cancellation", "-100.00", "-40.00"),
        ]
        assert usd["closing_balance"] == "-40.00"

    def test_one_cancelled_before_anyone_saw_it_was_never_billed(
        self, admin_client, account
    ):
        _invoice(
            account,
            "100.00",
            datetime.date(2026, 10, 2),
            status="Cancelled",
            cancelled_at=_noon(datetime.date(2026, 10, 3)),
        )
        assert _sections(admin_client.get(_url(account.id))) == {}


class TestPeriod:
    def test_defaults_to_this_month_so_far(self, admin_client, account):
        today = timezone.localdate()
        body = admin_client.get(f"/api/invoices/statements/{account.id}/").json()
        assert body["start_date"] == today.replace(day=1).isoformat()
        assert body["end_date"] == today.isoformat()

    @pytest.mark.parametrize("pdf", [False, True], ids=["json", "pdf"])
    def test_a_malformed_date_is_refused(self, admin_client, account, pdf):
        response = admin_client.get(
            _url(account.id, "start_date=10/01/2026&end_date=2026-10-31", pdf=pdf)
        )
        assert response.status_code == 400
        assert list(response.json()) == ["start_date"]

    def test_an_end_before_the_start_is_refused(self, admin_client, account):
        response = admin_client.get(
            _url(account.id, "start_date=2026-10-31&end_date=2026-10-01")
        )
        assert response.status_code == 400
        assert list(response.json()) == ["end_date"]

    def test_a_period_of_366_days_is_allowed(self, admin_client, account):
        response = admin_client.get(
            _url(account.id, "start_date=2026-01-01&end_date=2027-01-01")
        )
        assert response.status_code == 200, response.content

    def test_a_longer_period_is_refused(self, admin_client, account):
        response = admin_client.get(
            _url(account.id, "start_date=2026-01-01&end_date=2027-01-02")
        )
        assert response.status_code == 400
        assert response.json()["end_date"] == [
            "A statement can cover at most 366 days."
        ]


class TestPDF:
    def test_renders_a_pdf_named_for_the_period(self, admin_client, account):
        _invoice(account, "250.00", datetime.date(2026, 10, 5))

        response = admin_client.get(_url(account.id, pdf=True))

        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert response["Content-Disposition"] == (
            'attachment; filename="Statement_2026-10-01_2026-10-31.pdf"'
        )
        assert response.content.startswith(b"%PDF")

    def test_the_pdf_shows_the_balances_and_escapes_what_members_wrote(
        self, admin_client, org_a
    ):
        account = Account.objects.create(name="<b>Acme</b>", org=org_a)
        earlier = _invoice(account, "100.00", datetime.date(2026, 9, 10))
        _pay(earlier, "40.00", datetime.date(2026, 9, 20))
        october = _invoice(
            account, "250.00", datetime.date(2026, 10, 5), title="<i>Build</i>"
        )
        _pay(october, "100.00", datetime.date(2026, 10, 20))

        with patch("invoices.pdf.HTML") as html:
            response = admin_client.get(_url(account.id, pdf=True))

        assert response.status_code == 200
        rendered = html.call_args.kwargs["string"]
        assert "&lt;b&gt;Acme&lt;/b&gt;" in rendered
        assert "&lt;i&gt;Build&lt;/i&gt;" in rendered
        assert "<b>Acme" not in rendered and "<i>Build" not in rendered
        assert "$60.00" in rendered  # opening balance
        assert "$210.00" in rendered  # closing balance
        # A payment takes money off: the sign goes before the symbol.
        assert "-$100.00" in rendered
        assert "$-" not in rendered
