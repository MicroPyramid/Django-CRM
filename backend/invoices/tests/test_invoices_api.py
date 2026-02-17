import pytest
from unittest.mock import patch
from rest_framework.exceptions import PermissionDenied

from accounts.models import Account
from contacts.models import Contact
from invoices.models import Invoice, InvoiceLineItem, Payment


# ---------------------------------------------------------------------------
# Local fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def account_for_invoice(org_a):
    return Account.objects.create(name="Invoice Test Account", org=org_a)


@pytest.fixture
def contact_for_invoice(org_a):
    return Contact.objects.create(
        first_name="Test",
        last_name="Contact",
        email="testcontact@example.com",
        org=org_a,
    )


@pytest.fixture
def account_org_b(org_b):
    return Account.objects.create(name="Org B Account", org=org_b)


@pytest.fixture
def contact_org_b(org_b):
    return Contact.objects.create(
        first_name="OrgB",
        last_name="Contact",
        email="orgb@example.com",
        org=org_b,
    )


@pytest.fixture
def invoice(account_for_invoice, org_a):
    return Invoice.objects.create(
        invoice_title="Test Invoice",
        account=account_for_invoice,
        currency="USD",
        org=org_a,
    )


@pytest.fixture
def invoice_org_b(account_org_b, org_b):
    return Invoice.objects.create(
        invoice_title="Org B Invoice",
        account=account_org_b,
        currency="USD",
        org=org_b,
    )


# ---------------------------------------------------------------------------
# Invoice List / Create
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoiceListView:
    """Tests for GET /api/invoices/ and POST /api/invoices/."""

    def test_list_invoices(self, admin_client, invoice):
        response = admin_client.get("/api/invoices/")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["count"] >= 1

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_create_invoice(
        self,
        mock_history,
        admin_client,
        account_for_invoice,
        contact_for_invoice,
    ):
        response = admin_client.post(
            "/api/invoices/",
            {
                "invoice_title": "New Invoice",
                "account_id": str(account_for_invoice.id),
                "contact_id": str(contact_for_invoice.id),
                "currency": "USD",
            },
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["error"] is False
        assert data["message"] == "Invoice created successfully"
        assert "invoice" in data

    def test_create_invoice_unauthenticated(self, unauthenticated_client):
        with pytest.raises(PermissionDenied):
            unauthenticated_client.post(
                "/api/invoices/",
                {"invoice_title": "Unauthenticated Invoice"},
                format="json",
            )

    def test_org_isolation(self, org_b_client, invoice):
        """org_b_client should not see invoices belonging to org_a."""
        response = org_b_client.get("/api/invoices/")
        assert response.status_code == 200
        data = response.json()
        ids = [r["id"] for r in data["results"]]
        assert str(invoice.id) not in ids


# ---------------------------------------------------------------------------
# Invoice Detail / Update / Delete
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoiceDetailView:
    """Tests for GET/PUT/DELETE /api/invoices/<pk>/."""

    def test_get_detail(self, admin_client, invoice):
        response = admin_client.get(f"/api/invoices/{invoice.id}/")
        assert response.status_code == 200
        data = response.json()
        assert "invoice" in data
        assert data["invoice"]["id"] == str(invoice.id)

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_update_invoice(self, mock_history, admin_client, invoice):
        response = admin_client.put(
            f"/api/invoices/{invoice.id}/",
            {"invoice_title": "Updated Title"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert data["message"] == "Invoice updated successfully"

    def test_delete_invoice_not_supported(self, admin_client, invoice):
        """InvoiceDetailView does not implement DELETE; expect 405."""
        response = admin_client.delete(f"/api/invoices/{invoice.id}/")
        assert response.status_code == 405

    def test_cross_org(self, org_b_client, invoice):
        """org_b_client must not access an invoice belonging to org_a."""
        response = org_b_client.get(f"/api/invoices/{invoice.id}/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Invoice Actions (send, mark-paid, duplicate, cancel)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoiceActions:
    """Tests for invoice action endpoints."""

    @patch("invoices.api_views.send_invoice_to_client.delay")
    def test_send_invoice(self, mock_send, admin_client, invoice):
        response = admin_client.post(f"/api/invoices/{invoice.id}/send/")
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert data["message"] == "Invoice sent successfully"
        invoice.refresh_from_db()
        assert invoice.status == "Sent"

    def test_mark_paid(self, admin_client, invoice):
        response = admin_client.post(
            f"/api/invoices/{invoice.id}/mark-paid/",
            {
                "amount": "500.00",
                "payment_method": "BANK_TRANSFER",
                "payment_date": "2026-01-15",
            },
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert data["message"] == "Payment recorded successfully"
        assert "invoice" in data

    def test_duplicate_invoice(self, admin_client, invoice):
        response = admin_client.post(f"/api/invoices/{invoice.id}/duplicate/")
        assert response.status_code == 201
        data = response.json()
        assert data["error"] is False
        assert data["message"] == "Invoice duplicated successfully"
        assert "invoice" in data
        assert data["invoice"]["invoice_title"].startswith("Copy of")

    def test_cancel_invoice(self, admin_client, invoice):
        response = admin_client.post(f"/api/invoices/{invoice.id}/cancel/")
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert data["message"] == "Invoice cancelled successfully"
        invoice.refresh_from_db()
        assert invoice.status == "Cancelled"

    def test_cancel_already_cancelled(self, admin_client, invoice):
        invoice.status = "Cancelled"
        invoice.save()
        response = admin_client.post(f"/api/invoices/{invoice.id}/cancel/")
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True

    def test_cancel_paid_invoice(self, admin_client, invoice):
        invoice.status = "Paid"
        invoice.save()
        response = admin_client.post(f"/api/invoices/{invoice.id}/cancel/")
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True


# ---------------------------------------------------------------------------
# Invoice Line Items
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoiceLineItems:
    """Tests for /api/invoices/<invoice_id>/line-items/."""

    def test_create_line_item(self, admin_client, invoice):
        response = admin_client.post(
            f"/api/invoices/{invoice.id}/line-items/",
            {
                "name": "Consulting Hours",
                "quantity": "10.00",
                "unit_price": "150.00",
            },
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["error"] is False
        assert data["message"] == "Line item added"
        assert "line_item" in data

    def test_list_line_items(self, admin_client, invoice):
        InvoiceLineItem.objects.create(
            invoice=invoice,
            name="Widget A",
            quantity=5,
            unit_price=20,
            org=invoice.org,
        )
        response = admin_client.get(f"/api/invoices/{invoice.id}/line-items/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


# ---------------------------------------------------------------------------
# Invoice Payments
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoicePayments:
    """Tests for /api/invoices/<invoice_id>/payments/."""

    def test_create_payment(self, admin_client, invoice):
        response = admin_client.post(
            f"/api/invoices/{invoice.id}/payments/",
            {
                "amount": "250.00",
                "payment_date": "2026-02-01",
                "payment_method": "CREDIT_CARD",
            },
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["error"] is False
        assert data["message"] == "Payment recorded"
        assert "payment" in data

    def test_list_payments(self, admin_client, invoice):
        Payment.objects.create(
            invoice=invoice,
            amount=100,
            payment_date="2026-01-10",
            payment_method="CASH",
            org=invoice.org,
        )
        response = admin_client.get(f"/api/invoices/{invoice.id}/payments/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
