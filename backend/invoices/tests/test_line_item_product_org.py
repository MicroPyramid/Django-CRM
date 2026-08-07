"""A line item may not reference another organization's product.

``product`` is an auto-generated ``PrimaryKeyRelatedField`` on the three
line-item create serializers, so its queryset is ``Product.objects.all()``:
every org's catalogue. A member who knows a product UUID from another tenant
could name it on a line item and have it resolve, pulling that product's row
onto their own document.

``InvoiceCreateSerializer`` guarded this. ``EstimateCreateSerializer`` and
``RecurringInvoiceCreateSerializer`` are the same function without the check,
and the two standalone line-item routes built the serializer with no org
context at all, so neither could have checked. Five write paths, one guard
between them.

Both directions are pinned on every path: the cross-org product is refused,
and the org's own product still saves. A guard that rejects everything passes
the first half of that pair and breaks the feature.
"""

import datetime

import pytest
from django.utils import timezone
from rest_framework import status

from accounts.models import Account
from contacts.models import Contact
from invoices.models import Invoice, InvoiceLineItem, Product

INVOICES_URL = "/api/invoices/"
ESTIMATES_URL = "/api/invoices/estimates/"
RECURRING_URL = "/api/invoices/recurring/"

TODAY = timezone.localdate()


@pytest.fixture
def account_a(org_a):
    return Account.objects.create(name="Line Item Account", org=org_a)


@pytest.fixture
def contact_a(org_a):
    return Contact.objects.create(
        first_name="Line",
        last_name="Item",
        email="lineitem@example.com",
        org=org_a,
    )


@pytest.fixture
def product_a(org_a):
    return Product.objects.create(name="Own Widget", price=10, org=org_a)


@pytest.fixture
def product_b(org_b):
    """The other tenant's catalogue entry. Never reachable from org A."""
    return Product.objects.create(name="Foreign Widget", price=999, org=org_b)


def _line_item(product):
    return {
        "product": str(product.id),
        "name": "A line",
        "quantity": 1,
        "unit_price": "10.00",
    }


def _invoice_payload(account, contact, product):
    return {
        "invoice_title": "Invoice with a line item",
        "account_id": str(account.id),
        "contact_id": str(contact.id),
        "currency": "USD",
        "line_items": [_line_item(product)],
    }


def _estimate_payload(account, contact, product):
    return {
        "title": "Estimate with a line item",
        "account_id": str(account.id),
        "contact_id": str(contact.id),
        "currency": "USD",
        "issue_date": str(TODAY),
        "expiry_date": str(TODAY + datetime.timedelta(days=30)),
        "line_items": [_line_item(product)],
    }


def _recurring_payload(account, contact, product):
    return {
        "title": "Recurring with a line item",
        "account_id": str(account.id),
        "contact_id": str(contact.id),
        "frequency": "MONTHLY",
        "start_date": str(TODAY),
        "next_generation_date": str(TODAY),
        "payment_terms": "NET_30",
        "currency": "USD",
        "is_active": True,
        "line_items": [_line_item(product)],
    }


@pytest.mark.django_db
class TestNestedCreateRefusesAForeignProduct:
    def test_invoice_create(self, admin_client, account_a, contact_a, product_b):
        response = admin_client.post(
            INVOICES_URL,
            _invoice_payload(account_a, contact_a, product_b),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "line_items" in response.json()["errors"]

    def test_estimate_create(self, admin_client, account_a, contact_a, product_b):
        response = admin_client.post(
            ESTIMATES_URL,
            _estimate_payload(account_a, contact_a, product_b),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            "an estimate accepted a line item pointing at another org's product"
        )
        assert "line_items" in response.json()["errors"]

    def test_recurring_create(self, admin_client, account_a, contact_a, product_b):
        response = admin_client.post(
            RECURRING_URL,
            _recurring_payload(account_a, contact_a, product_b),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            "a recurring invoice accepted a line item pointing at another org's product"
        )
        assert "line_items" in response.json()["errors"]


@pytest.mark.django_db
class TestNestedCreateStillAcceptsOwnProduct:
    """The False direction. Without these the guard could be `return False`."""

    def test_invoice_create(self, admin_client, account_a, contact_a, product_a):
        response = admin_client.post(
            INVOICES_URL,
            _invoice_payload(account_a, contact_a, product_a),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.content

    def test_estimate_create(self, admin_client, account_a, contact_a, product_a):
        response = admin_client.post(
            ESTIMATES_URL,
            _estimate_payload(account_a, contact_a, product_a),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.content

    def test_recurring_create(self, admin_client, account_a, contact_a, product_a):
        response = admin_client.post(
            RECURRING_URL,
            _recurring_payload(account_a, contact_a, product_a),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.content

    def test_a_line_item_with_no_product_is_still_allowed(
        self, admin_client, account_a, contact_a
    ):
        """`product` is optional. The guard must not have made it required."""
        response = admin_client.post(
            INVOICES_URL,
            {
                "invoice_title": "Ad hoc invoice",
                "account_id": str(account_a.id),
                "contact_id": str(contact_a.id),
                "currency": "USD",
                "line_items": [
                    {"name": "Ad hoc work", "quantity": 2, "unit_price": "50.00"}
                ],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.content


@pytest.mark.django_db
class TestNestedUpdateRefusesAForeignProduct:
    """`validate()` runs on update too, which is the path a PUT takes."""

    def test_invoice_put(self, admin_client, org_a, account_a, contact_a, product_b):
        invoice = Invoice.objects.create(
            invoice_title="Existing", account=account_a, currency="USD", org=org_a
        )
        response = admin_client.put(
            f"{INVOICES_URL}{invoice.id}/",
            {
                "account_id": str(account_a.id),
                "contact_id": str(contact_a.id),
                "line_items": [_line_item(product_b)],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not InvoiceLineItem.objects.filter(invoice=invoice).exists()


@pytest.mark.django_db
class TestStandaloneLineItemRoutes:
    """These build the serializer directly, so they need their own org context."""

    @pytest.fixture
    def invoice(self, org_a, account_a):
        return Invoice.objects.create(
            invoice_title="Standalone target",
            account=account_a,
            currency="USD",
            org=org_a,
        )

    def test_post_refuses_a_foreign_product(self, admin_client, invoice, product_b):
        response = admin_client.post(
            f"{INVOICES_URL}{invoice.id}/line-items/",
            _line_item(product_b),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            "the standalone line-item route attached another org's product"
        )
        assert "product" in response.json()["errors"]
        assert not InvoiceLineItem.objects.filter(invoice=invoice).exists()

    def test_post_accepts_own_product(self, admin_client, invoice, product_a):
        response = admin_client.post(
            f"{INVOICES_URL}{invoice.id}/line-items/",
            _line_item(product_a),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.content
        assert InvoiceLineItem.objects.filter(
            invoice=invoice, product=product_a
        ).exists()

    def test_put_refuses_a_foreign_product(
        self, admin_client, org_a, invoice, product_a, product_b
    ):
        line_item = InvoiceLineItem.objects.create(
            invoice=invoice,
            org=org_a,
            product=product_a,
            name="A line",
            quantity=1,
            unit_price=10,
        )
        response = admin_client.put(
            f"{INVOICES_URL}{invoice.id}/line-items/{line_item.id}/",
            {"product": str(product_b.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            "an existing line item was repointed at another org's product"
        )
        line_item.refresh_from_db()
        assert line_item.product_id == product_a.id

    def test_put_accepts_own_product(self, admin_client, org_a, invoice, product_a):
        line_item = InvoiceLineItem.objects.create(
            invoice=invoice,
            org=org_a,
            name="A line",
            quantity=1,
            unit_price=10,
        )
        response = admin_client.put(
            f"{INVOICES_URL}{invoice.id}/line-items/{line_item.id}/",
            {"product": str(product_a.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK, response.content
        line_item.refresh_from_db()
        assert line_item.product_id == product_a.id
