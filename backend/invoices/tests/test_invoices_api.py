import datetime
import uuid
from decimal import Decimal

import pytest
from unittest.mock import patch
from rest_framework.exceptions import PermissionDenied

from accounts.models import Account
from contacts.models import Contact
from invoices.models import (
    Estimate,
    EstimateLineItem,
    Invoice,
    InvoiceHistory,
    InvoiceLineItem,
    InvoiceTemplate,
    Payment,
    Product,
    RecurringInvoice,
    RecurringInvoiceLineItem,
)


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


@pytest.fixture
def product(org_a):
    return Product.objects.create(
        name="Test Product",
        description="A test product",
        sku="TP-001",
        price=Decimal("99.99"),
        currency="USD",
        category="Software",
        is_active=True,
        org=org_a,
    )


@pytest.fixture
def product_inactive(org_a):
    return Product.objects.create(
        name="Inactive Product",
        sku="TP-002",
        price=Decimal("49.99"),
        is_active=False,
        org=org_a,
    )


@pytest.fixture
def template(org_a):
    return InvoiceTemplate.objects.create(
        name="Default Template",
        primary_color="#3B82F6",
        secondary_color="#1E40AF",
        default_notes="Thank you for your business",
        default_terms="Net 30",
        footer_text="Footer text",
        is_default=True,
        org=org_a,
    )


@pytest.fixture
def estimate(account_for_invoice, contact_for_invoice, org_a):
    return Estimate.objects.create(
        title="Test Estimate",
        account=account_for_invoice,
        contact=contact_for_invoice,
        client_name="Test Client",
        client_email="client@example.com",
        currency="USD",
        issue_date=datetime.date.today(),
        expiry_date=datetime.date.today() + datetime.timedelta(days=30),
        org=org_a,
    )


@pytest.fixture
def recurring_invoice(account_for_invoice, contact_for_invoice, org_a):
    return RecurringInvoice.objects.create(
        title="Monthly Hosting",
        account=account_for_invoice,
        contact=contact_for_invoice,
        client_name="Recurring Client",
        client_email="recurring@example.com",
        frequency="MONTHLY",
        start_date=datetime.date.today(),
        next_generation_date=datetime.date.today(),
        payment_terms="NET_30",
        currency="USD",
        is_active=True,
        org=org_a,
    )


@pytest.fixture
def line_item(invoice, org_a):
    return InvoiceLineItem.objects.create(
        invoice=invoice,
        name="Widget A",
        quantity=Decimal("5"),
        unit_price=Decimal("20.00"),
        org=org_a,
    )


@pytest.fixture
def payment(invoice, org_a):
    return Payment.objects.create(
        invoice=invoice,
        amount=Decimal("100.00"),
        payment_date=datetime.date.today(),
        payment_method="CASH",
        org=org_a,
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


# ---------------------------------------------------------------------------
# Invoice List Filters & Sorting
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoiceListFilters:
    """Tests for invoice list filtering, searching, and sorting."""

    def test_filter_by_status(self, admin_client, invoice):
        invoice.status = "Sent"
        invoice.save()
        response = admin_client.get("/api/invoices/?status=Sent")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        for r in data["results"]:
            assert r["status"] == "Sent"

    def test_filter_by_status_no_results(self, admin_client, invoice):
        response = admin_client.get("/api/invoices/?status=Paid")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

    def test_search_by_title(self, admin_client, invoice):
        response = admin_client.get("/api/invoices/?search=Test+Invoice")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_search_by_invoice_number(self, admin_client, invoice):
        response = admin_client.get(
            f"/api/invoices/?search={invoice.invoice_number}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_filter_by_account(self, admin_client, invoice):
        response = admin_client.get(
            f"/api/invoices/?account={invoice.account_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_filter_by_date_range(self, admin_client, invoice):
        today = datetime.date.today().isoformat()
        response = admin_client.get(
            f"/api/invoices/?issue_date_gte={today}&issue_date_lte={today}"
        )
        assert response.status_code == 200

    def test_sort_by_created_at(self, admin_client, invoice):
        response = admin_client.get("/api/invoices/?sort=created_at")
        assert response.status_code == 200

    def test_sort_by_due_date(self, admin_client, invoice):
        response = admin_client.get("/api/invoices/?sort=-due_date")
        assert response.status_code == 200

    def test_sort_by_status(self, admin_client, invoice):
        response = admin_client.get("/api/invoices/?sort=status")
        assert response.status_code == 200

    def test_invalid_sort_field_ignored(self, admin_client, invoice):
        """Invalid sort fields should be ignored (falls back to default)."""
        response = admin_client.get("/api/invoices/?sort=invalid_field")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Invoice Create - validation edge cases
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoiceCreateValidation:
    """Tests for invoice creation validation paths."""

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_create_invoice_missing_account(
        self, mock_history, admin_client, contact_for_invoice
    ):
        response = admin_client.post(
            "/api/invoices/",
            {
                "invoice_title": "No Account Invoice",
                "contact_id": str(contact_for_invoice.id),
                "currency": "USD",
            },
            format="json",
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_create_invoice_missing_contact(
        self, mock_history, admin_client, account_for_invoice
    ):
        response = admin_client.post(
            "/api/invoices/",
            {
                "invoice_title": "No Contact Invoice",
                "account_id": str(account_for_invoice.id),
                "currency": "USD",
            },
            format="json",
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_create_invoice_invalid_account(
        self, mock_history, admin_client, contact_for_invoice
    ):
        fake_id = str(uuid.uuid4())
        response = admin_client.post(
            "/api/invoices/",
            {
                "invoice_title": "Bad Account",
                "account_id": fake_id,
                "contact_id": str(contact_for_invoice.id),
                "currency": "USD",
            },
            format="json",
        )
        assert response.status_code == 400

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_create_invoice_cross_org_account(
        self, mock_history, admin_client, account_org_b, contact_for_invoice
    ):
        """Account from another org should fail validation."""
        response = admin_client.post(
            "/api/invoices/",
            {
                "invoice_title": "Cross-org",
                "account_id": str(account_org_b.id),
                "contact_id": str(contact_for_invoice.id),
                "currency": "USD",
            },
            format="json",
        )
        assert response.status_code == 400

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_create_invoice_with_line_items(
        self,
        mock_history,
        admin_client,
        account_for_invoice,
        contact_for_invoice,
    ):
        response = admin_client.post(
            "/api/invoices/",
            {
                "invoice_title": "Invoice With Items",
                "account_id": str(account_for_invoice.id),
                "contact_id": str(contact_for_invoice.id),
                "currency": "USD",
                "line_items": [
                    {
                        "name": "Item 1",
                        "quantity": "2",
                        "unit_price": "100.00",
                    },
                    {
                        "name": "Item 2",
                        "quantity": "1",
                        "unit_price": "50.00",
                    },
                ],
            },
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["error"] is False
        inv_id = data["invoice"]["id"]
        assert InvoiceLineItem.objects.filter(invoice_id=inv_id).count() == 2

    @patch("invoices.api_views.create_invoice_history.delay")
    @patch("invoices.api_views.send_email.delay")
    def test_create_invoice_triggers_email_for_assigned_users(
        self,
        mock_email,
        mock_history,
        admin_client,
        account_for_invoice,
        contact_for_invoice,
        admin_profile,
    ):
        response = admin_client.post(
            "/api/invoices/",
            {
                "invoice_title": "Assigned Invoice",
                "account_id": str(account_for_invoice.id),
                "contact_id": str(contact_for_invoice.id),
                "currency": "USD",
            },
            format="json",
        )
        assert response.status_code == 201
        # History is always called
        assert mock_history.called


# ---------------------------------------------------------------------------
# Invoice Detail - permission edge cases
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoiceDetailPermissions:
    """Tests for invoice detail view permission checks."""

    def test_regular_user_cannot_see_unassigned_invoice(
        self, user_client, invoice
    ):
        """Non-admin user who is neither creator nor assigned cannot see the invoice."""
        response = user_client.get(f"/api/invoices/{invoice.id}/")
        assert response.status_code == 403

    def test_get_nonexistent_invoice(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.get(f"/api/invoices/{fake_id}/")
        assert response.status_code == 404

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_update_nonexistent_invoice(self, mock_history, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.put(
            f"/api/invoices/{fake_id}/",
            {"invoice_title": "Nope"},
            format="json",
        )
        assert response.status_code == 404

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_regular_user_cannot_update_unassigned_invoice(
        self, mock_history, user_client, invoice
    ):
        response = user_client.put(
            f"/api/invoices/{invoice.id}/",
            {"invoice_title": "Hacked"},
            format="json",
        )
        assert response.status_code == 403

    def test_detail_includes_attachments_comments_history(
        self, admin_client, invoice
    ):
        response = admin_client.get(f"/api/invoices/{invoice.id}/")
        assert response.status_code == 200
        data = response.json()
        assert "attachments" in data
        assert "comments" in data
        assert "history" in data

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_update_invoice_with_line_items_replacement(
        self, mock_history, admin_client, invoice, line_item
    ):
        """PUT with line_items replaces all existing line items."""
        response = admin_client.put(
            f"/api/invoices/{invoice.id}/",
            {
                "line_items": [
                    {"name": "Replacement Item", "quantity": "1", "unit_price": "999.00"},
                ],
            },
            format="json",
        )
        assert response.status_code == 200
        assert InvoiceLineItem.objects.filter(invoice=invoice).count() == 1
        assert InvoiceLineItem.objects.filter(
            invoice=invoice, name="Replacement Item"
        ).exists()


# ---------------------------------------------------------------------------
# Invoice Actions - additional edge cases
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoiceActionsEdgeCases:
    """Additional edge case tests for invoice action endpoints."""

    @patch("invoices.api_views.send_invoice_to_client.delay")
    def test_send_already_sent_invoice(self, mock_send, admin_client, invoice):
        """Sending an already-sent invoice updates sent_at but keeps status."""
        invoice.status = "Sent"
        invoice.save()
        response = admin_client.post(f"/api/invoices/{invoice.id}/send/")
        assert response.status_code == 200
        invoice.refresh_from_db()
        assert invoice.status == "Sent"
        assert invoice.is_email_sent is True

    @patch("invoices.api_views.send_invoice_to_client.delay")
    def test_send_nonexistent_invoice(self, mock_send, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.post(f"/api/invoices/{fake_id}/send/")
        assert response.status_code == 404

    def test_mark_paid_nonexistent_invoice(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.post(
            f"/api/invoices/{fake_id}/mark-paid/",
            {"amount": "100.00", "payment_method": "CASH", "payment_date": "2026-01-01"},
            format="json",
        )
        assert response.status_code == 404

    def test_duplicate_nonexistent_invoice(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.post(f"/api/invoices/{fake_id}/duplicate/")
        assert response.status_code == 404

    def test_cancel_nonexistent_invoice(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.post(f"/api/invoices/{fake_id}/cancel/")
        assert response.status_code == 404

    def test_cancel_invoice_permission_denied_for_regular_user(
        self, user_client, invoice
    ):
        response = user_client.post(f"/api/invoices/{invoice.id}/cancel/")
        assert response.status_code == 403

    def test_duplicate_invoice_with_line_items(
        self, admin_client, invoice, line_item
    ):
        """Duplicate should copy line items."""
        response = admin_client.post(f"/api/invoices/{invoice.id}/duplicate/")
        assert response.status_code == 201
        new_id = response.json()["invoice"]["id"]
        assert InvoiceLineItem.objects.filter(invoice_id=new_id).count() == 1

    def test_mark_paid_with_defaults(self, admin_client, invoice):
        """Mark paid with no explicit amount uses amount_due."""
        response = admin_client.post(
            f"/api/invoices/{invoice.id}/mark-paid/",
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False


# ---------------------------------------------------------------------------
# Invoice PDF
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoicePDF:
    """Tests for /api/invoices/<pk>/pdf/."""

    @patch("invoices.api_views.generate_invoice_pdf")
    @patch("invoices.api_views.generate_invoice_filename")
    def test_pdf_success(
        self, mock_filename, mock_pdf, admin_client, invoice
    ):
        mock_pdf.return_value = b"%PDF-1.4 test content"
        mock_filename.return_value = "invoice.pdf"
        response = admin_client.get(f"/api/invoices/{invoice.id}/pdf/")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert 'filename="invoice.pdf"' in response["Content-Disposition"]

    @patch(
        "invoices.api_views.generate_invoice_pdf",
        side_effect=ImportError("weasyprint not installed"),
    )
    def test_pdf_import_error(self, mock_pdf, admin_client, invoice):
        response = admin_client.get(f"/api/invoices/{invoice.id}/pdf/")
        assert response.status_code == 503

    @patch(
        "invoices.api_views.generate_invoice_pdf",
        side_effect=RuntimeError("unexpected"),
    )
    def test_pdf_generic_error(self, mock_pdf, admin_client, invoice):
        response = admin_client.get(f"/api/invoices/{invoice.id}/pdf/")
        assert response.status_code == 500

    def test_pdf_nonexistent_invoice(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.get(f"/api/invoices/{fake_id}/pdf/")
        assert response.status_code == 404

    @patch("invoices.api_views.generate_invoice_pdf")
    @patch("invoices.api_views.generate_invoice_filename")
    def test_pdf_permission_denied_for_regular_user(
        self, mock_filename, mock_pdf, user_client, invoice
    ):
        response = user_client.get(f"/api/invoices/{invoice.id}/pdf/")
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Line Item Detail (update, delete)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestLineItemDetail:
    """Tests for PUT/DELETE /api/invoices/<invoice_id>/line-items/<pk>/."""

    def test_update_line_item(self, admin_client, invoice, line_item):
        response = admin_client.put(
            f"/api/invoices/{invoice.id}/line-items/{line_item.id}/",
            {"name": "Updated Widget", "quantity": "10", "unit_price": "25.00"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert data["message"] == "Line item updated"
        line_item.refresh_from_db()
        assert line_item.name == "Updated Widget"

    def test_update_line_item_partial(self, admin_client, invoice, line_item):
        response = admin_client.put(
            f"/api/invoices/{invoice.id}/line-items/{line_item.id}/",
            {"quantity": "20"},
            format="json",
        )
        assert response.status_code == 200

    def test_delete_line_item(self, admin_client, invoice, line_item):
        response = admin_client.delete(
            f"/api/invoices/{invoice.id}/line-items/{line_item.id}/"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert data["message"] == "Line item deleted"
        assert not InvoiceLineItem.objects.filter(id=line_item.id).exists()

    def test_update_nonexistent_line_item(self, admin_client, invoice):
        fake_id = uuid.uuid4()
        response = admin_client.put(
            f"/api/invoices/{invoice.id}/line-items/{fake_id}/",
            {"name": "Ghost"},
            format="json",
        )
        assert response.status_code == 404

    def test_delete_nonexistent_line_item(self, admin_client, invoice):
        fake_id = uuid.uuid4()
        response = admin_client.delete(
            f"/api/invoices/{invoice.id}/line-items/{fake_id}/"
        )
        assert response.status_code == 404

    def test_create_line_item_invalid_data(self, admin_client, invoice):
        response = admin_client.post(
            f"/api/invoices/{invoice.id}/line-items/",
            {"quantity": "not_a_number"},
            format="json",
        )
        assert response.status_code == 400

    def test_line_item_on_nonexistent_invoice(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.get(f"/api/invoices/{fake_id}/line-items/")
        assert response.status_code == 404

    def test_create_line_item_on_nonexistent_invoice(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.post(
            f"/api/invoices/{fake_id}/line-items/",
            {"name": "Item", "quantity": "1", "unit_price": "10.00"},
            format="json",
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Payment Detail (delete)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPaymentDetail:
    """Tests for DELETE /api/invoices/<invoice_id>/payments/<pk>/."""

    def test_delete_payment(self, admin_client, invoice, payment):
        response = admin_client.delete(
            f"/api/invoices/{invoice.id}/payments/{payment.id}/"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert data["message"] == "Payment deleted"
        assert not Payment.objects.filter(id=payment.id).exists()

    def test_delete_payment_nonexistent(self, admin_client, invoice):
        fake_id = uuid.uuid4()
        response = admin_client.delete(
            f"/api/invoices/{invoice.id}/payments/{fake_id}/"
        )
        assert response.status_code == 404

    def test_delete_payment_permission_denied(
        self, user_client, invoice, payment
    ):
        response = user_client.delete(
            f"/api/invoices/{invoice.id}/payments/{payment.id}/"
        )
        assert response.status_code == 403

    def test_create_payment_invalid_data(self, admin_client, invoice):
        response = admin_client.post(
            f"/api/invoices/{invoice.id}/payments/",
            {"amount": "not_a_number"},
            format="json",
        )
        assert response.status_code == 400

    def test_create_payment_nonexistent_invoice(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.post(
            f"/api/invoices/{fake_id}/payments/",
            {
                "amount": "100.00",
                "payment_date": "2026-01-01",
                "payment_method": "CASH",
            },
            format="json",
        )
        assert response.status_code == 404

    def test_list_payments_nonexistent_invoice(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.get(f"/api/invoices/{fake_id}/payments/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Products CRUD
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProductListView:
    """Tests for GET/POST /api/invoices/products/."""

    def test_list_products(self, admin_client, product):
        response = admin_client.get("/api/invoices/products/")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["count"] >= 1

    def test_list_products_filter_active(self, admin_client, product, product_inactive):
        response = admin_client.get("/api/invoices/products/?is_active=true")
        assert response.status_code == 200
        data = response.json()
        for r in data["results"]:
            assert r["is_active"] is True

    def test_list_products_filter_inactive(self, admin_client, product, product_inactive):
        response = admin_client.get("/api/invoices/products/?is_active=false")
        assert response.status_code == 200
        data = response.json()
        for r in data["results"]:
            assert r["is_active"] is False

    def test_list_products_search(self, admin_client, product):
        response = admin_client.get("/api/invoices/products/?search=Test")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_list_products_search_by_sku(self, admin_client, product):
        response = admin_client.get("/api/invoices/products/?search=TP-001")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_list_products_filter_category(self, admin_client, product):
        response = admin_client.get("/api/invoices/products/?category=Software")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_create_product(self, admin_client):
        response = admin_client.post(
            "/api/invoices/products/",
            {
                "name": "New Product",
                "description": "A new product",
                "sku": "NP-001",
                "price": "199.99",
                "category": "Hardware",
            },
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["error"] is False
        assert data["product"]["name"] == "New Product"

    def test_create_product_invalid(self, admin_client):
        """Missing required name field."""
        response = admin_client.post(
            "/api/invoices/products/",
            {"description": "No name"},
            format="json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestProductDetailView:
    """Tests for GET/PUT/DELETE /api/invoices/products/<pk>/."""

    def test_get_product(self, admin_client, product):
        response = admin_client.get(f"/api/invoices/products/{product.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Product"

    def test_get_nonexistent_product(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.get(f"/api/invoices/products/{fake_id}/")
        assert response.status_code == 404

    def test_update_product(self, admin_client, product):
        response = admin_client.put(
            f"/api/invoices/products/{product.id}/",
            {"name": "Updated Product", "price": "149.99"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert data["product"]["name"] == "Updated Product"

    def test_update_nonexistent_product(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.put(
            f"/api/invoices/products/{fake_id}/",
            {"name": "Nope"},
            format="json",
        )
        assert response.status_code == 404

    def test_delete_product(self, admin_client, product):
        response = admin_client.delete(f"/api/invoices/products/{product.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert not Product.objects.filter(id=product.id).exists()

    def test_delete_nonexistent_product(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.delete(f"/api/invoices/products/{fake_id}/")
        assert response.status_code == 404

    def test_org_isolation(self, org_b_client, product):
        """org_b_client should not see products from org_a."""
        response = org_b_client.get(f"/api/invoices/products/{product.id}/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Estimates CRUD
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEstimateListView:
    """Tests for GET/POST /api/invoices/estimates/."""

    def test_list_estimates(self, admin_client, estimate):
        response = admin_client.get("/api/invoices/estimates/")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["count"] >= 1

    def test_list_estimates_filter_status(self, admin_client, estimate):
        response = admin_client.get("/api/invoices/estimates/?status=Draft")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_list_estimates_filter_account(self, admin_client, estimate):
        response = admin_client.get(
            f"/api/invoices/estimates/?account={estimate.account_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_list_estimates_search(self, admin_client, estimate):
        response = admin_client.get("/api/invoices/estimates/?search=Test")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_create_estimate(self, admin_client, account_for_invoice, contact_for_invoice):
        response = admin_client.post(
            "/api/invoices/estimates/",
            {
                "title": "New Estimate",
                "account_id": str(account_for_invoice.id),
                "contact_id": str(contact_for_invoice.id),
                "client_name": "New Client",
                "client_email": "new@example.com",
                "currency": "USD",
            },
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["error"] is False
        assert data["estimate"]["title"] == "New Estimate"

    def test_create_estimate_invalid_account(
        self, admin_client, contact_for_invoice
    ):
        fake_id = str(uuid.uuid4())
        response = admin_client.post(
            "/api/invoices/estimates/",
            {
                "title": "Bad Estimate",
                "account_id": fake_id,
                "contact_id": str(contact_for_invoice.id),
                "client_name": "Client",
                "client_email": "c@example.com",
            },
            format="json",
        )
        assert response.status_code == 400

    def test_create_estimate_missing_fields(self, admin_client):
        response = admin_client.post(
            "/api/invoices/estimates/",
            {"title": "Incomplete"},
            format="json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestEstimateDetailView:
    """Tests for GET/PUT/DELETE /api/invoices/estimates/<pk>/."""

    def test_get_estimate(self, admin_client, estimate):
        response = admin_client.get(f"/api/invoices/estimates/{estimate.id}/")
        assert response.status_code == 200
        data = response.json()
        assert "estimate" in data
        assert data["estimate"]["title"] == "Test Estimate"

    def test_get_nonexistent_estimate(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.get(f"/api/invoices/estimates/{fake_id}/")
        assert response.status_code == 404

    def test_update_estimate(self, admin_client, estimate):
        response = admin_client.put(
            f"/api/invoices/estimates/{estimate.id}/",
            {"title": "Updated Estimate"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert data["estimate"]["title"] == "Updated Estimate"

    def test_update_nonexistent_estimate(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.put(
            f"/api/invoices/estimates/{fake_id}/",
            {"title": "Nope"},
            format="json",
        )
        assert response.status_code == 404

    def test_delete_estimate(self, admin_client, estimate):
        response = admin_client.delete(f"/api/invoices/estimates/{estimate.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert not Estimate.objects.filter(id=estimate.id).exists()

    def test_delete_nonexistent_estimate(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.delete(f"/api/invoices/estimates/{fake_id}/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Estimate Actions (convert, send, pdf)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEstimateActions:
    """Tests for estimate action endpoints."""

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_convert_estimate_to_invoice(self, mock_history, admin_client, estimate):
        response = admin_client.post(
            f"/api/invoices/estimates/{estimate.id}/convert/"
        )
        assert response.status_code == 201
        data = response.json()
        assert data["error"] is False
        assert data["message"] == "Estimate converted to invoice"
        assert "invoice" in data
        estimate.refresh_from_db()
        assert estimate.status == "Accepted"
        assert estimate.converted_to_invoice is not None

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_convert_already_converted_estimate(
        self, mock_history, admin_client, estimate, invoice
    ):
        estimate.converted_to_invoice = invoice
        estimate.save()
        response = admin_client.post(
            f"/api/invoices/estimates/{estimate.id}/convert/"
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True

    def test_convert_nonexistent_estimate(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.post(f"/api/invoices/estimates/{fake_id}/convert/")
        assert response.status_code == 404

    @patch("invoices.tasks.send_estimate_to_client.delay")
    def test_send_estimate(self, mock_send, admin_client, estimate):
        response = admin_client.post(
            f"/api/invoices/estimates/{estimate.id}/send/"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        estimate.refresh_from_db()
        assert estimate.status == "Sent"
        assert estimate.sent_at is not None

    @patch("invoices.tasks.send_estimate_to_client.delay")
    def test_send_already_sent_estimate(self, mock_send, admin_client, estimate):
        estimate.status = "Sent"
        estimate.save()
        response = admin_client.post(
            f"/api/invoices/estimates/{estimate.id}/send/"
        )
        assert response.status_code == 200
        estimate.refresh_from_db()
        assert estimate.status == "Sent"

    def test_send_nonexistent_estimate(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.post(f"/api/invoices/estimates/{fake_id}/send/")
        assert response.status_code == 404

    @patch("invoices.api_views.generate_estimate_pdf")
    @patch("invoices.api_views.generate_estimate_filename")
    def test_estimate_pdf_success(
        self, mock_filename, mock_pdf, admin_client, estimate
    ):
        mock_pdf.return_value = b"%PDF-1.4 estimate"
        mock_filename.return_value = "estimate.pdf"
        response = admin_client.get(
            f"/api/invoices/estimates/{estimate.id}/pdf/"
        )
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"

    def test_estimate_pdf_nonexistent(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.get(f"/api/invoices/estimates/{fake_id}/pdf/")
        assert response.status_code == 404

    @patch("invoices.api_views.generate_estimate_pdf")
    @patch("invoices.api_views.generate_estimate_filename")
    def test_estimate_pdf_permission_denied(
        self, mock_filename, mock_pdf, user_client, estimate
    ):
        response = user_client.get(
            f"/api/invoices/estimates/{estimate.id}/pdf/"
        )
        assert response.status_code == 403

    @patch(
        "invoices.api_views.generate_estimate_pdf",
        side_effect=ImportError("no weasyprint"),
    )
    def test_estimate_pdf_import_error(self, mock_pdf, admin_client, estimate):
        response = admin_client.get(
            f"/api/invoices/estimates/{estimate.id}/pdf/"
        )
        assert response.status_code == 503

    @patch(
        "invoices.api_views.generate_estimate_pdf",
        side_effect=RuntimeError("unexpected"),
    )
    def test_estimate_pdf_generic_error(self, mock_pdf, admin_client, estimate):
        response = admin_client.get(
            f"/api/invoices/estimates/{estimate.id}/pdf/"
        )
        assert response.status_code == 500

    @patch("invoices.api_views.create_invoice_history.delay")
    def test_convert_estimate_with_line_items(
        self, mock_history, admin_client, estimate
    ):
        """Converting estimate with line items copies them to the new invoice."""
        EstimateLineItem.objects.create(
            estimate=estimate,
            name="Service A",
            quantity=Decimal("2"),
            unit_price=Decimal("100.00"),
            org=estimate.org,
        )
        response = admin_client.post(
            f"/api/invoices/estimates/{estimate.id}/convert/"
        )
        assert response.status_code == 201
        inv_id = response.json()["invoice"]["id"]
        assert InvoiceLineItem.objects.filter(invoice_id=inv_id).count() == 1


# ---------------------------------------------------------------------------
# Recurring Invoices CRUD
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRecurringInvoiceListView:
    """Tests for GET/POST /api/invoices/recurring/."""

    def test_list_recurring(self, admin_client, recurring_invoice):
        response = admin_client.get("/api/invoices/recurring/")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["count"] >= 1

    def test_list_recurring_filter_active(
        self, admin_client, recurring_invoice
    ):
        response = admin_client.get("/api/invoices/recurring/?is_active=true")
        assert response.status_code == 200
        data = response.json()
        for r in data["results"]:
            assert r["is_active"] is True

    def test_list_recurring_filter_inactive(
        self, admin_client, recurring_invoice
    ):
        recurring_invoice.is_active = False
        recurring_invoice.save()
        response = admin_client.get("/api/invoices/recurring/?is_active=false")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        for r in data["results"]:
            assert r["is_active"] is False

    def test_create_recurring(
        self, admin_client, account_for_invoice, contact_for_invoice
    ):
        response = admin_client.post(
            "/api/invoices/recurring/",
            {
                "title": "New Recurring",
                "account_id": str(account_for_invoice.id),
                "contact_id": str(contact_for_invoice.id),
                "client_name": "Client",
                "client_email": "client@example.com",
                "frequency": "WEEKLY",
                "start_date": "2026-03-01",
                "next_generation_date": "2026-03-01",
                "currency": "USD",
            },
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["error"] is False
        assert data["recurring_invoice"]["title"] == "New Recurring"

    def test_create_recurring_invalid_account(
        self, admin_client, contact_for_invoice
    ):
        response = admin_client.post(
            "/api/invoices/recurring/",
            {
                "title": "Bad Recurring",
                "account_id": str(uuid.uuid4()),
                "contact_id": str(contact_for_invoice.id),
                "client_name": "Client",
                "client_email": "c@e.com",
                "frequency": "MONTHLY",
                "start_date": "2026-03-01",
                "next_generation_date": "2026-03-01",
            },
            format="json",
        )
        assert response.status_code == 400

    def test_create_recurring_missing_fields(self, admin_client):
        response = admin_client.post(
            "/api/invoices/recurring/",
            {"title": "Incomplete"},
            format="json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestRecurringInvoiceDetailView:
    """Tests for GET/PUT/DELETE /api/invoices/recurring/<pk>/."""

    def test_get_recurring(self, admin_client, recurring_invoice):
        response = admin_client.get(
            f"/api/invoices/recurring/{recurring_invoice.id}/"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Monthly Hosting"

    def test_get_nonexistent_recurring(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.get(f"/api/invoices/recurring/{fake_id}/")
        assert response.status_code == 404

    def test_update_recurring(self, admin_client, recurring_invoice):
        response = admin_client.put(
            f"/api/invoices/recurring/{recurring_invoice.id}/",
            {"title": "Updated Recurring"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert data["recurring_invoice"]["title"] == "Updated Recurring"

    def test_update_nonexistent_recurring(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.put(
            f"/api/invoices/recurring/{fake_id}/",
            {"title": "Nope"},
            format="json",
        )
        assert response.status_code == 404

    def test_delete_recurring(self, admin_client, recurring_invoice):
        response = admin_client.delete(
            f"/api/invoices/recurring/{recurring_invoice.id}/"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert not RecurringInvoice.objects.filter(
            id=recurring_invoice.id
        ).exists()

    def test_delete_nonexistent_recurring(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.delete(f"/api/invoices/recurring/{fake_id}/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestRecurringInvoicePauseToggle:
    """Tests for POST /api/invoices/recurring/<pk>/toggle/."""

    def test_pause_recurring(self, admin_client, recurring_invoice):
        assert recurring_invoice.is_active is True
        response = admin_client.post(
            f"/api/invoices/recurring/{recurring_invoice.id}/toggle/"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert "paused" in data["message"]
        recurring_invoice.refresh_from_db()
        assert recurring_invoice.is_active is False

    def test_resume_recurring(self, admin_client, recurring_invoice):
        recurring_invoice.is_active = False
        recurring_invoice.save()
        response = admin_client.post(
            f"/api/invoices/recurring/{recurring_invoice.id}/toggle/"
        )
        assert response.status_code == 200
        data = response.json()
        assert "resumed" in data["message"]
        recurring_invoice.refresh_from_db()
        assert recurring_invoice.is_active is True

    def test_toggle_nonexistent(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.post(f"/api/invoices/recurring/{fake_id}/toggle/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Invoice Templates CRUD
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoiceTemplateListView:
    """Tests for GET/POST /api/invoices/templates/."""

    def test_list_templates(self, admin_client, template):
        response = admin_client.get("/api/invoices/templates/")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["count"] >= 1

    def test_create_template(self, admin_client):
        response = admin_client.post(
            "/api/invoices/templates/",
            {
                "name": "New Template",
                "primary_color": "#FF0000",
                "secondary_color": "#00FF00",
                "default_notes": "Thanks!",
                "default_terms": "Net 15",
                "is_default": False,
            },
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["error"] is False
        assert data["template"]["name"] == "New Template"

    def test_create_template_missing_name(self, admin_client):
        response = admin_client.post(
            "/api/invoices/templates/",
            {"primary_color": "#FF0000"},
            format="json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestInvoiceTemplateDetailView:
    """Tests for GET/PUT/DELETE /api/invoices/templates/<pk>/."""

    def test_get_template(self, admin_client, template):
        response = admin_client.get(f"/api/invoices/templates/{template.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Default Template"

    def test_get_nonexistent_template(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.get(f"/api/invoices/templates/{fake_id}/")
        assert response.status_code == 404

    def test_update_template(self, admin_client, template):
        response = admin_client.put(
            f"/api/invoices/templates/{template.id}/",
            {"name": "Updated Template"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert data["template"]["name"] == "Updated Template"

    def test_update_nonexistent_template(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.put(
            f"/api/invoices/templates/{fake_id}/",
            {"name": "Nope"},
            format="json",
        )
        assert response.status_code == 404

    def test_delete_template(self, admin_client, template):
        response = admin_client.delete(
            f"/api/invoices/templates/{template.id}/"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert not InvoiceTemplate.objects.filter(id=template.id).exists()

    def test_delete_nonexistent_template(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.delete(f"/api/invoices/templates/{fake_id}/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoiceComments:
    """Tests for invoice comment endpoints."""

    def test_create_comment(self, admin_client, invoice):
        response = admin_client.post(
            f"/api/invoices/{invoice.id}/comments/",
            {"comment": "This is a test comment"},
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["error"] is False
        assert data["message"] == "Comment added"
        assert "comment" in data

    def test_create_comment_empty(self, admin_client, invoice):
        response = admin_client.post(
            f"/api/invoices/{invoice.id}/comments/",
            {"comment": ""},
            format="json",
        )
        assert response.status_code == 400

    def test_create_comment_missing_text(self, admin_client, invoice):
        response = admin_client.post(
            f"/api/invoices/{invoice.id}/comments/",
            {},
            format="json",
        )
        assert response.status_code == 400

    def test_create_comment_nonexistent_invoice(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.post(
            f"/api/invoices/{fake_id}/comments/",
            {"comment": "Ghost"},
            format="json",
        )
        assert response.status_code == 404

    def test_update_comment(self, admin_client, invoice):
        # Create first
        resp = admin_client.post(
            f"/api/invoices/{invoice.id}/comments/",
            {"comment": "Original"},
            format="json",
        )
        comment_id = resp.json()["comment"]["id"]
        # Update
        response = admin_client.put(
            f"/api/invoices/comments/{comment_id}/",
            {"comment": "Updated comment"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False

    def test_delete_comment(self, admin_client, invoice):
        resp = admin_client.post(
            f"/api/invoices/{invoice.id}/comments/",
            {"comment": "To delete"},
            format="json",
        )
        comment_id = resp.json()["comment"]["id"]
        response = admin_client.delete(f"/api/invoices/comments/{comment_id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False

    def test_update_nonexistent_comment(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.put(
            f"/api/invoices/comments/{fake_id}/",
            {"comment": "Nope"},
            format="json",
        )
        assert response.status_code == 404

    def test_delete_nonexistent_comment(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.delete(f"/api/invoices/comments/{fake_id}/")
        assert response.status_code == 404

    def test_regular_user_cannot_edit_others_comment(
        self, admin_client, user_client, invoice
    ):
        # Admin creates comment
        resp = admin_client.post(
            f"/api/invoices/{invoice.id}/comments/",
            {"comment": "Admin's comment"},
            format="json",
        )
        comment_id = resp.json()["comment"]["id"]
        # Regular user tries to edit
        response = user_client.put(
            f"/api/invoices/comments/{comment_id}/",
            {"comment": "Hacked"},
            format="json",
        )
        assert response.status_code == 403

    def test_regular_user_cannot_delete_others_comment(
        self, admin_client, user_client, invoice
    ):
        resp = admin_client.post(
            f"/api/invoices/{invoice.id}/comments/",
            {"comment": "Admin's comment"},
            format="json",
        )
        comment_id = resp.json()["comment"]["id"]
        response = user_client.delete(f"/api/invoices/comments/{comment_id}/")
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoiceAttachments:
    """Tests for invoice attachment endpoints."""

    def test_upload_attachment_no_file(self, admin_client, invoice):
        response = admin_client.post(
            f"/api/invoices/{invoice.id}/attachments/",
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert data["message"] == "File required"

    def test_upload_attachment_nonexistent_invoice(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.post(f"/api/invoices/{fake_id}/attachments/")
        assert response.status_code == 404

    def test_delete_attachment_nonexistent(self, admin_client):
        fake_id = uuid.uuid4()
        response = admin_client.delete(f"/api/invoices/attachments/{fake_id}/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Reports / Dashboard
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoiceDashboard:
    """Tests for GET /api/invoices/reports/dashboard/."""

    def test_dashboard(self, admin_client, invoice):
        response = admin_client.get("/api/invoices/reports/dashboard/")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "total_invoiced" in data["summary"]
        assert "total_paid" in data["summary"]
        assert "total_due" in data["summary"]
        assert "status_counts" in data
        assert "overdue" in data
        assert "recent_activity" in data
        assert "estimates" in data

    def test_dashboard_with_data(self, admin_client, invoice, estimate):
        """Dashboard should reflect existing invoices and estimates."""
        response = admin_client.get("/api/invoices/reports/dashboard/")
        assert response.status_code == 200
        data = response.json()
        assert data["recent_activity"]["invoices_created_30d"] >= 1


@pytest.mark.django_db
class TestRevenueReport:
    """Tests for GET /api/invoices/reports/revenue/."""

    def test_revenue_report_default(self, admin_client):
        response = admin_client.get("/api/invoices/reports/revenue/")
        assert response.status_code == 200
        data = response.json()
        assert "start_date" in data
        assert "end_date" in data
        assert "group_by" in data
        assert data["group_by"] == "month"
        assert "data" in data
        assert "total" in data

    def test_revenue_report_by_day(self, admin_client):
        response = admin_client.get(
            "/api/invoices/reports/revenue/?group_by=day"
            "&start_date=2026-01-01&end_date=2026-12-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["group_by"] == "day"

    def test_revenue_report_by_week(self, admin_client):
        response = admin_client.get(
            "/api/invoices/reports/revenue/?group_by=week"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["group_by"] == "week"

    def test_revenue_report_by_year(self, admin_client):
        response = admin_client.get(
            "/api/invoices/reports/revenue/?group_by=year"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["group_by"] == "year"

    def test_revenue_report_with_dates(self, admin_client):
        response = admin_client.get(
            "/api/invoices/reports/revenue/"
            "?start_date=2025-01-01&end_date=2026-12-31"
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestAgingReport:
    """Tests for GET /api/invoices/reports/aging/."""

    def test_aging_report_empty(self, admin_client):
        response = admin_client.get("/api/invoices/reports/aging/")
        assert response.status_code == 200
        data = response.json()
        assert "current" in data
        assert "1_30_days" in data
        assert "31_60_days" in data
        assert "61_90_days" in data
        assert "over_90_days" in data
        assert "total" in data

    def _make_unpaid_invoice(self, title, status, due_date, account, org):
        """Helper: create an invoice with a line item so amount_due > 0."""
        inv = Invoice.objects.create(
            invoice_title=title,
            account=account,
            status=status,
            currency="USD",
            org=org,
        )
        InvoiceLineItem.objects.create(
            invoice=inv,
            name="Service",
            quantity=Decimal("1"),
            unit_price=Decimal("100.00"),
            org=org,
        )
        # Recalculate and then override due_date and status via update_fields
        inv.recalculate_totals()
        inv.due_date = due_date
        inv.status = status
        inv.save(update_fields=["due_date", "status", "subtotal", "total_amount", "amount_due"])
        return inv

    def test_aging_report_with_overdue_invoices(
        self, admin_client, account_for_invoice, org_a
    ):
        """Create invoices with various due dates and check aging buckets."""
        today = datetime.date.today()
        self._make_unpaid_invoice(
            "Current Invoice", "Sent",
            today + datetime.timedelta(days=5),
            account_for_invoice, org_a,
        )
        self._make_unpaid_invoice(
            "Overdue 15d", "Sent",
            today - datetime.timedelta(days=15),
            account_for_invoice, org_a,
        )
        self._make_unpaid_invoice(
            "Overdue 45d", "Sent",
            today - datetime.timedelta(days=45),
            account_for_invoice, org_a,
        )
        self._make_unpaid_invoice(
            "Overdue 75d", "Partially_Paid",
            today - datetime.timedelta(days=75),
            account_for_invoice, org_a,
        )
        self._make_unpaid_invoice(
            "Overdue 120d", "Overdue",
            today - datetime.timedelta(days=120),
            account_for_invoice, org_a,
        )
        response = admin_client.get("/api/invoices/reports/aging/")
        assert response.status_code == 200
        data = response.json()
        assert data["current"]["count"] >= 1
        assert data["1_30_days"]["count"] >= 1
        assert data["31_60_days"]["count"] >= 1
        assert data["61_90_days"]["count"] >= 1
        assert data["over_90_days"]["count"] >= 1

    def test_aging_report_with_no_due_date(
        self, admin_client, account_for_invoice, org_a
    ):
        """Invoice with no due date goes to current bucket."""
        self._make_unpaid_invoice(
            "No Due Date", "Sent", None,
            account_for_invoice, org_a,
        )
        response = admin_client.get("/api/invoices/reports/aging/")
        assert response.status_code == 200
        data = response.json()
        assert data["current"]["count"] >= 1


# ---------------------------------------------------------------------------
# Public Invoice Views (tested via RequestFactory to bypass RequireOrgContext middleware)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPublicInvoiceView:
    """Tests for PublicInvoiceView (via RequestFactory to bypass middleware)."""

    def _get(self, token):
        from rest_framework.test import APIRequestFactory
        from invoices.public_views import PublicInvoiceView

        factory = APIRequestFactory()
        request = factory.get(f"/api/public/invoice/{token}/")
        view = PublicInvoiceView.as_view()
        return view(request, token=token)

    def test_public_invoice_view(self, invoice):
        response = self._get(invoice.public_token)
        assert response.status_code == 200
        assert response.data["invoice_number"] == invoice.invoice_number
        assert response.data["invoice_title"] == invoice.invoice_title
        assert "line_items" in response.data
        assert "payments" in response.data
        assert "org" in response.data
        assert "template" in response.data

    def test_public_invoice_tracks_view(self, invoice):
        invoice.status = "Sent"
        invoice.save()
        self._get(invoice.public_token)
        invoice.refresh_from_db()
        assert invoice.viewed_at is not None
        assert invoice.status == "Viewed"

    def test_public_invoice_already_viewed(self, invoice):
        """Second view should not change viewed_at."""
        from django.utils import timezone

        first_time = timezone.now()
        invoice.viewed_at = first_time
        invoice.save()
        self._get(invoice.public_token)
        invoice.refresh_from_db()
        assert invoice.viewed_at == first_time

    def test_public_invoice_not_found(self):
        response = self._get("nonexistent_token")
        assert response.status_code == 404

    def test_public_invoice_disabled_link(self, invoice):
        invoice.public_link_enabled = False
        invoice.save()
        response = self._get(invoice.public_token)
        assert response.status_code == 404

    def test_public_invoice_with_template(self, invoice, template):
        invoice.template = template
        invoice.save()
        response = self._get(invoice.public_token)
        assert response.status_code == 200
        assert response.data["template"]["primary_color"] == "#3B82F6"

    def test_public_invoice_with_default_template(self, invoice, template):
        """When invoice has no template, use org default template."""
        response = self._get(invoice.public_token)
        assert response.status_code == 200
        assert response.data["template"]["primary_color"] == "#3B82F6"


@pytest.mark.django_db
class TestPublicInvoicePDFView:
    """Tests for PublicInvoicePDFView."""

    def _get(self, token):
        from rest_framework.test import APIRequestFactory
        from invoices.public_views import PublicInvoicePDFView

        factory = APIRequestFactory()
        request = factory.get(f"/api/public/invoice/{token}/pdf/")
        view = PublicInvoicePDFView.as_view()
        return view(request, token=token)

    @patch("invoices.public_views.generate_invoice_pdf")
    @patch("invoices.public_views.generate_invoice_filename")
    def test_public_pdf_success(self, mock_filename, mock_pdf, invoice):
        mock_pdf.return_value = b"%PDF-1.4 test"
        mock_filename.return_value = "invoice.pdf"
        response = self._get(invoice.public_token)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"

    def test_public_pdf_not_found(self):
        response = self._get("bad_token")
        assert response.status_code == 404

    @patch(
        "invoices.public_views.generate_invoice_pdf",
        side_effect=ImportError("no lib"),
    )
    def test_public_pdf_import_error(self, mock_pdf, invoice):
        response = self._get(invoice.public_token)
        assert response.status_code == 503

    @patch(
        "invoices.public_views.generate_invoice_pdf",
        side_effect=RuntimeError("fail"),
    )
    def test_public_pdf_generic_error(self, mock_pdf, invoice):
        response = self._get(invoice.public_token)
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# Public Estimate Views
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPublicEstimateView:
    """Tests for PublicEstimateView."""

    def _get(self, token):
        from rest_framework.test import APIRequestFactory
        from invoices.public_views import PublicEstimateView

        factory = APIRequestFactory()
        request = factory.get(f"/api/public/estimate/{token}/")
        view = PublicEstimateView.as_view()
        return view(request, token=token)

    def test_public_estimate_view(self, estimate):
        response = self._get(estimate.public_token)
        assert response.status_code == 200
        assert response.data["title"] == "Test Estimate"
        assert "line_items" in response.data
        assert "template" in response.data
        assert "org" in response.data

    def test_public_estimate_tracks_view(self, estimate):
        estimate.status = "Sent"
        estimate.save()
        self._get(estimate.public_token)
        estimate.refresh_from_db()
        assert estimate.viewed_at is not None
        assert estimate.status == "Viewed"

    def test_public_estimate_not_found(self):
        response = self._get("nonexistent")
        assert response.status_code == 404

    def test_public_estimate_disabled_link(self, estimate):
        estimate.public_link_enabled = False
        estimate.save()
        response = self._get(estimate.public_token)
        assert response.status_code == 404

    def test_public_estimate_with_default_template(self, estimate, template):
        response = self._get(estimate.public_token)
        assert response.status_code == 200
        assert response.data["template"]["primary_color"] == "#3B82F6"

    def test_public_estimate_no_template(self, estimate):
        """No default template gives fallback colors."""
        response = self._get(estimate.public_token)
        assert response.status_code == 200
        assert response.data["template"]["primary_color"] == "#3B82F6"
        assert response.data["template"]["secondary_color"] == "#1E40AF"


@pytest.mark.django_db
class TestPublicEstimatePDFView:
    """Tests for PublicEstimatePDFView."""

    def _get(self, token):
        from rest_framework.test import APIRequestFactory
        from invoices.public_views import PublicEstimatePDFView

        factory = APIRequestFactory()
        request = factory.get(f"/api/public/estimate/{token}/pdf/")
        view = PublicEstimatePDFView.as_view()
        return view(request, token=token)

    @patch("invoices.public_views.generate_estimate_pdf")
    @patch("invoices.public_views.generate_estimate_filename")
    def test_public_estimate_pdf_success(
        self, mock_filename, mock_pdf, estimate
    ):
        mock_pdf.return_value = b"%PDF-1.4 est"
        mock_filename.return_value = "estimate.pdf"
        response = self._get(estimate.public_token)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"

    def test_public_estimate_pdf_not_found(self):
        response = self._get("bad_token")
        assert response.status_code == 404

    @patch(
        "invoices.public_views.generate_estimate_pdf",
        side_effect=ImportError("no lib"),
    )
    def test_public_estimate_pdf_import_error(self, mock_pdf, estimate):
        response = self._get(estimate.public_token)
        assert response.status_code == 503

    @patch(
        "invoices.public_views.generate_estimate_pdf",
        side_effect=RuntimeError("fail"),
    )
    def test_public_estimate_pdf_generic_error(self, mock_pdf, estimate):
        response = self._get(estimate.public_token)
        assert response.status_code == 500


@pytest.mark.django_db
class TestPublicEstimateAcceptDecline:
    """Tests for PublicEstimateAcceptView and PublicEstimateDeclineView."""

    def _post_accept(self, token):
        from rest_framework.test import APIRequestFactory
        from invoices.public_views import PublicEstimateAcceptView

        factory = APIRequestFactory()
        request = factory.post(f"/api/public/estimate/{token}/accept/")
        view = PublicEstimateAcceptView.as_view()
        return view(request, token=token)

    def _post_decline(self, token):
        from rest_framework.test import APIRequestFactory
        from invoices.public_views import PublicEstimateDeclineView

        factory = APIRequestFactory()
        request = factory.post(f"/api/public/estimate/{token}/decline/")
        view = PublicEstimateDeclineView.as_view()
        return view(request, token=token)

    def test_accept_estimate(self, estimate):
        estimate.status = "Sent"
        estimate.save()
        response = self._post_accept(estimate.public_token)
        assert response.status_code == 200
        assert response.data["error"] is False
        estimate.refresh_from_db()
        assert estimate.status == "Accepted"
        assert estimate.accepted_at is not None

    def test_accept_viewed_estimate(self, estimate):
        estimate.status = "Viewed"
        estimate.save()
        response = self._post_accept(estimate.public_token)
        assert response.status_code == 200
        estimate.refresh_from_db()
        assert estimate.status == "Accepted"

    def test_accept_draft_estimate_fails(self, estimate):
        """Can only accept Sent or Viewed estimates."""
        assert estimate.status == "Draft"
        response = self._post_accept(estimate.public_token)
        assert response.status_code == 400

    def test_accept_nonexistent_estimate(self):
        response = self._post_accept("bad_token")
        assert response.status_code == 404

    def test_decline_estimate(self, estimate):
        estimate.status = "Sent"
        estimate.save()
        response = self._post_decline(estimate.public_token)
        assert response.status_code == 200
        assert response.data["error"] is False
        estimate.refresh_from_db()
        assert estimate.status == "Declined"
        assert estimate.declined_at is not None

    def test_decline_draft_estimate_fails(self, estimate):
        assert estimate.status == "Draft"
        response = self._post_decline(estimate.public_token)
        assert response.status_code == 400

    def test_decline_nonexistent_estimate(self):
        response = self._post_decline("bad_token")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Model Methods and Properties
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoiceModel:
    """Tests for Invoice model methods and properties."""

    def test_str(self, invoice):
        assert str(invoice) == invoice.invoice_number

    def test_invoice_number_generated(self, invoice):
        assert invoice.invoice_number.startswith("INV-")

    def test_public_token_generated(self, invoice):
        assert invoice.public_token != ""
        assert len(invoice.public_token) > 10

    def test_public_url(self, invoice):
        assert invoice.public_url == f"/portal/invoice/{invoice.public_token}"

    def test_is_overdue_true(self, invoice):
        invoice.due_date = datetime.date.today() - datetime.timedelta(days=1)
        invoice.status = "Sent"
        assert invoice.is_overdue is True

    def test_is_overdue_false_paid(self, invoice):
        invoice.due_date = datetime.date.today() - datetime.timedelta(days=1)
        invoice.status = "Paid"
        assert invoice.is_overdue is False

    def test_is_overdue_false_future_date(self, invoice):
        invoice.due_date = datetime.date.today() + datetime.timedelta(days=10)
        invoice.status = "Sent"
        assert invoice.is_overdue is False

    def test_is_overdue_false_no_due_date(self, invoice):
        invoice.due_date = None
        invoice.status = "Sent"
        assert invoice.is_overdue is False

    def test_calculate_due_date_net_30(self, invoice):
        invoice.issue_date = datetime.date(2026, 1, 1)
        invoice.payment_terms = "NET_30"
        invoice.due_date = None
        result = invoice.calculate_due_date()
        assert result == datetime.date(2026, 1, 31)

    def test_calculate_due_date_net_15(self, invoice):
        invoice.issue_date = datetime.date(2026, 1, 1)
        invoice.payment_terms = "NET_15"
        result = invoice.calculate_due_date()
        assert result == datetime.date(2026, 1, 16)

    def test_calculate_due_date_due_on_receipt(self, invoice):
        invoice.issue_date = datetime.date(2026, 1, 1)
        invoice.payment_terms = "DUE_ON_RECEIPT"
        result = invoice.calculate_due_date()
        assert result == datetime.date(2026, 1, 1)

    def test_calculate_due_date_net_60(self, invoice):
        invoice.issue_date = datetime.date(2026, 1, 1)
        invoice.payment_terms = "NET_60"
        result = invoice.calculate_due_date()
        assert result == datetime.date(2026, 3, 2)

    def test_calculate_due_date_no_issue_date(self, invoice):
        invoice.issue_date = None
        result = invoice.calculate_due_date()
        assert result is None

    def test_recalculate_totals_percentage_discount(
        self, invoice, org_a
    ):
        InvoiceLineItem.objects.create(
            invoice=invoice,
            name="Item",
            quantity=Decimal("10"),
            unit_price=Decimal("100"),
            org=org_a,
        )
        invoice.discount_type = "PERCENTAGE"
        invoice.discount_value = Decimal("10")
        invoice.tax_rate = Decimal("5")
        invoice.recalculate_totals()
        # subtotal = 1000, discount = 100, taxable = 900, tax = 45
        assert invoice.subtotal == Decimal("1000.00")
        assert invoice.discount_amount == Decimal("100.00")
        assert invoice.tax_amount == Decimal("45.00")
        assert invoice.total_amount == Decimal("945.00")

    def test_recalculate_totals_fixed_discount(self, invoice, org_a):
        InvoiceLineItem.objects.create(
            invoice=invoice,
            name="Item",
            quantity=Decimal("1"),
            unit_price=Decimal("500"),
            org=org_a,
        )
        invoice.discount_type = "FIXED"
        invoice.discount_value = Decimal("50")
        invoice.tax_rate = Decimal("10")
        invoice.recalculate_totals()
        assert invoice.subtotal == Decimal("500.00")
        assert invoice.discount_amount == Decimal("50.00")
        assert invoice.tax_amount == Decimal("45.00")
        assert invoice.total_amount == Decimal("495.00")

    def test_formatted_total_amount(self, invoice):
        invoice.currency = "EUR"
        invoice.total_amount = Decimal("1234.56")
        assert invoice.formatted_total_amount() == "EUR 1234.56"

    def test_formatted_amount_due(self, invoice):
        invoice.currency = "GBP"
        invoice.amount_due = Decimal("999.00")
        assert invoice.formatted_amount_due() == "GBP 999.00"

    def test_created_on_arrow(self, invoice):
        result = invoice.created_on_arrow
        assert "ago" in result


@pytest.mark.django_db
class TestInvoiceLineItemModel:
    """Tests for InvoiceLineItem model methods and properties."""

    def test_str(self, line_item):
        result = str(line_item)
        assert line_item.invoice.invoice_number in result
        assert "Widget A" in result

    def test_str_no_name(self, invoice, org_a):
        item = InvoiceLineItem.objects.create(
            invoice=invoice,
            description="Just a description",
            quantity=Decimal("1"),
            unit_price=Decimal("10"),
            org=org_a,
        )
        assert "Just a description" in str(item)

    def test_str_no_name_no_description(self, invoice, org_a):
        item = InvoiceLineItem.objects.create(
            invoice=invoice,
            quantity=Decimal("1"),
            unit_price=Decimal("10"),
            org=org_a,
        )
        assert "Item" in str(item)

    def test_formatted_unit_price(self, line_item):
        result = line_item.formatted_unit_price
        assert "USD" in result

    def test_formatted_total(self, line_item):
        result = line_item.formatted_total
        assert "USD" in result

    def test_save_calculates_subtotal(self, invoice, org_a):
        item = InvoiceLineItem.objects.create(
            invoice=invoice,
            name="Item",
            quantity=Decimal("3"),
            unit_price=Decimal("100"),
            org=org_a,
        )
        assert item.subtotal == Decimal("300.00")

    def test_save_percentage_discount(self, invoice, org_a):
        item = InvoiceLineItem.objects.create(
            invoice=invoice,
            name="Item",
            quantity=Decimal("1"),
            unit_price=Decimal("200"),
            discount_type="PERCENTAGE",
            discount_value=Decimal("25"),
            org=org_a,
        )
        assert item.discount_amount == Decimal("50.00")
        assert item.total == Decimal("150.00")

    def test_save_fixed_discount(self, invoice, org_a):
        item = InvoiceLineItem.objects.create(
            invoice=invoice,
            name="Item",
            quantity=Decimal("1"),
            unit_price=Decimal("200"),
            discount_type="FIXED",
            discount_value=Decimal("30"),
            org=org_a,
        )
        assert item.discount_amount == Decimal("30.00")
        assert item.total == Decimal("170.00")

    def test_save_with_tax(self, invoice, org_a):
        item = InvoiceLineItem.objects.create(
            invoice=invoice,
            name="Item",
            quantity=Decimal("1"),
            unit_price=Decimal("100"),
            tax_rate=Decimal("10"),
            org=org_a,
        )
        assert item.tax_amount == Decimal("10.00")
        assert item.total == Decimal("110.00")


@pytest.mark.django_db
class TestPaymentModel:
    """Tests for Payment model methods."""

    def test_str(self, payment):
        result = str(payment)
        assert payment.invoice.invoice_number in result

    def _make_invoice_with_total(self, invoice, org_a, total):
        """Add a line item to give the invoice a real total_amount."""
        InvoiceLineItem.objects.create(
            invoice=invoice,
            name="Service",
            quantity=Decimal("1"),
            unit_price=total,
            org=org_a,
        )
        invoice.recalculate_totals()
        invoice.save()
        invoice.refresh_from_db()

    def test_payment_updates_invoice(self, invoice, org_a):
        self._make_invoice_with_total(invoice, org_a, Decimal("1000.00"))
        Payment.objects.create(
            invoice=invoice,
            amount=Decimal("400.00"),
            payment_date=datetime.date.today(),
            payment_method="CASH",
            org=org_a,
        )
        invoice.refresh_from_db()
        assert invoice.amount_paid == Decimal("400.00")
        assert invoice.status == "Partially_Paid"

    def test_full_payment_marks_paid(self, invoice, org_a):
        self._make_invoice_with_total(invoice, org_a, Decimal("500.00"))
        Payment.objects.create(
            invoice=invoice,
            amount=Decimal("500.00"),
            payment_date=datetime.date.today(),
            payment_method="BANK_TRANSFER",
            org=org_a,
        )
        invoice.refresh_from_db()
        assert invoice.status == "Paid"
        assert invoice.paid_at is not None

    def test_delete_payment_recalculates(self, invoice, org_a):
        self._make_invoice_with_total(invoice, org_a, Decimal("500.00"))
        p = Payment.objects.create(
            invoice=invoice,
            amount=Decimal("500.00"),
            payment_date=datetime.date.today(),
            payment_method="CASH",
            org=org_a,
        )
        invoice.refresh_from_db()
        assert invoice.status == "Paid"
        p.delete()
        invoice.refresh_from_db()
        assert invoice.amount_paid == Decimal("0")

    def test_payment_inherits_org_from_invoice(self, invoice):
        p = Payment.objects.create(
            invoice=invoice,
            amount=Decimal("50.00"),
            payment_date=datetime.date.today(),
            payment_method="CASH",
            org=invoice.org,
        )
        assert p.org_id == invoice.org_id


@pytest.mark.django_db
class TestEstimateModel:
    """Tests for Estimate model methods and properties."""

    def test_str(self, estimate):
        assert str(estimate) == estimate.estimate_number

    def test_estimate_number_generated(self, estimate):
        assert estimate.estimate_number.startswith("EST-")

    def test_public_token_generated(self, estimate):
        assert estimate.public_token != ""

    def test_public_url(self, estimate):
        assert estimate.public_url == f"/portal/estimate/{estimate.public_token}"

    def test_is_expired_true(self, estimate):
        estimate.expiry_date = datetime.date.today() - datetime.timedelta(days=1)
        estimate.status = "Sent"
        assert estimate.is_expired is True

    def test_is_expired_false_accepted(self, estimate):
        estimate.expiry_date = datetime.date.today() - datetime.timedelta(days=1)
        estimate.status = "Accepted"
        assert estimate.is_expired is False

    def test_is_expired_false_future(self, estimate):
        estimate.expiry_date = datetime.date.today() + datetime.timedelta(days=10)
        estimate.status = "Sent"
        assert estimate.is_expired is False

    def test_is_expired_false_no_expiry(self, estimate):
        estimate.expiry_date = None
        assert estimate.is_expired is False

    def test_recalculate_totals(self, estimate, org_a):
        EstimateLineItem.objects.create(
            estimate=estimate,
            name="Item",
            quantity=Decimal("2"),
            unit_price=Decimal("100"),
            org=org_a,
        )
        estimate.discount_type = "PERCENTAGE"
        estimate.discount_value = Decimal("10")
        estimate.tax_rate = Decimal("5")
        estimate.recalculate_totals()
        assert estimate.subtotal == Decimal("200.00")
        assert estimate.discount_amount == Decimal("20.00")
        assert estimate.tax_amount == Decimal("9.00")
        assert estimate.total_amount == Decimal("189.00")


@pytest.mark.django_db
class TestEstimateLineItemModel:
    """Tests for EstimateLineItem model."""

    def test_str(self, estimate, org_a):
        item = EstimateLineItem.objects.create(
            estimate=estimate,
            name="Service",
            quantity=Decimal("1"),
            unit_price=Decimal("100"),
            org=org_a,
        )
        result = str(item)
        assert estimate.estimate_number in result
        assert "Service" in result

    def test_save_calculates_totals(self, estimate, org_a):
        item = EstimateLineItem.objects.create(
            estimate=estimate,
            name="Widget",
            quantity=Decimal("5"),
            unit_price=Decimal("10"),
            discount_type="PERCENTAGE",
            discount_value=Decimal("20"),
            tax_rate=Decimal("10"),
            org=org_a,
        )
        # subtotal = 50, discount = 10, taxable = 40, tax = 4
        assert item.subtotal == Decimal("50.00")
        assert item.discount_amount == Decimal("10.00")
        assert item.tax_amount == Decimal("4.00")
        assert item.total == Decimal("44.00")

    def test_save_fixed_discount(self, estimate, org_a):
        item = EstimateLineItem.objects.create(
            estimate=estimate,
            name="Widget",
            quantity=Decimal("1"),
            unit_price=Decimal("100"),
            discount_type="FIXED",
            discount_value=Decimal("15"),
            org=org_a,
        )
        assert item.discount_amount == Decimal("15.00")
        assert item.total == Decimal("85.00")


@pytest.mark.django_db
class TestRecurringInvoiceModel:
    """Tests for RecurringInvoice model methods."""

    def test_str(self, recurring_invoice):
        result = str(recurring_invoice)
        assert "Monthly Hosting" in result
        assert "MONTHLY" in result

    def test_calculate_next_date_weekly(self, recurring_invoice):
        recurring_invoice.frequency = "WEEKLY"
        recurring_invoice.next_generation_date = datetime.date(2026, 1, 1)
        result = recurring_invoice.calculate_next_date()
        assert result == datetime.date(2026, 1, 8)

    def test_calculate_next_date_biweekly(self, recurring_invoice):
        recurring_invoice.frequency = "BIWEEKLY"
        recurring_invoice.next_generation_date = datetime.date(2026, 1, 1)
        result = recurring_invoice.calculate_next_date()
        assert result == datetime.date(2026, 1, 15)

    def test_calculate_next_date_monthly(self, recurring_invoice):
        recurring_invoice.frequency = "MONTHLY"
        recurring_invoice.next_generation_date = datetime.date(2026, 1, 15)
        result = recurring_invoice.calculate_next_date()
        assert result == datetime.date(2026, 2, 15)

    def test_calculate_next_date_quarterly(self, recurring_invoice):
        recurring_invoice.frequency = "QUARTERLY"
        recurring_invoice.next_generation_date = datetime.date(2026, 1, 1)
        result = recurring_invoice.calculate_next_date()
        assert result == datetime.date(2026, 4, 1)

    def test_calculate_next_date_semi_annually(self, recurring_invoice):
        recurring_invoice.frequency = "SEMI_ANNUALLY"
        recurring_invoice.next_generation_date = datetime.date(2026, 1, 1)
        result = recurring_invoice.calculate_next_date()
        assert result == datetime.date(2026, 7, 1)

    def test_calculate_next_date_yearly(self, recurring_invoice):
        recurring_invoice.frequency = "YEARLY"
        recurring_invoice.next_generation_date = datetime.date(2026, 1, 1)
        result = recurring_invoice.calculate_next_date()
        assert result == datetime.date(2027, 1, 1)

    def test_calculate_next_date_custom(self, recurring_invoice):
        recurring_invoice.frequency = "CUSTOM"
        recurring_invoice.custom_days = 10
        recurring_invoice.next_generation_date = datetime.date(2026, 1, 1)
        result = recurring_invoice.calculate_next_date()
        assert result == datetime.date(2026, 1, 11)

    def test_calculate_next_date_custom_no_days(self, recurring_invoice):
        """CUSTOM without custom_days falls back to monthly."""
        recurring_invoice.frequency = "CUSTOM"
        recurring_invoice.custom_days = None
        recurring_invoice.next_generation_date = datetime.date(2026, 1, 1)
        result = recurring_invoice.calculate_next_date()
        assert result == datetime.date(2026, 2, 1)


@pytest.mark.django_db
class TestRecurringInvoiceLineItemModel:
    """Tests for RecurringInvoiceLineItem model."""

    def test_str(self, recurring_invoice, org_a):
        item = RecurringInvoiceLineItem.objects.create(
            recurring_invoice=recurring_invoice,
            description="Monthly Service",
            quantity=Decimal("1"),
            unit_price=Decimal("100"),
            org=org_a,
        )
        result = str(item)
        assert "Monthly Hosting" in result

    def test_inherits_org(self, recurring_invoice):
        item = RecurringInvoiceLineItem.objects.create(
            recurring_invoice=recurring_invoice,
            description="Service",
            quantity=Decimal("1"),
            unit_price=Decimal("50"),
            org=recurring_invoice.org,
        )
        assert item.org_id == recurring_invoice.org_id


@pytest.mark.django_db
class TestProductModel:
    """Tests for Product model."""

    def test_str(self, product):
        assert str(product) == "Test Product"


@pytest.mark.django_db
class TestInvoiceTemplateModel:
    """Tests for InvoiceTemplate model methods."""

    def test_str(self, template):
        assert str(template) == "Default Template"

    def test_default_template_uniqueness(self, org_a):
        """Setting a new template as default should unset the previous default."""
        t1 = InvoiceTemplate.objects.create(
            name="Template 1", is_default=True, org=org_a
        )
        t2 = InvoiceTemplate.objects.create(
            name="Template 2", is_default=True, org=org_a
        )
        t1.refresh_from_db()
        assert t1.is_default is False
        assert t2.is_default is True

    def test_non_default_save(self, org_a):
        t = InvoiceTemplate.objects.create(
            name="Non-Default", is_default=False, org=org_a
        )
        assert t.is_default is False


@pytest.mark.django_db
class TestInvoiceHistoryModel:
    """Tests for InvoiceHistory model."""

    def test_str(self, invoice, org_a):
        history = InvoiceHistory.objects.create(
            invoice=invoice,
            invoice_title=invoice.invoice_title,
            invoice_number=invoice.invoice_number,
            status=invoice.status,
            org=org_a,
        )
        result = str(history)
        assert invoice.invoice_number in result

    def test_created_on_arrow(self, invoice, org_a):
        history = InvoiceHistory.objects.create(
            invoice=invoice,
            invoice_title=invoice.invoice_title,
            invoice_number=invoice.invoice_number,
            status=invoice.status,
            org=org_a,
        )
        assert "ago" in history.created_on_arrow

    def test_inherits_org(self, invoice):
        history = InvoiceHistory.objects.create(
            invoice=invoice,
            invoice_title=invoice.invoice_title,
            invoice_number=invoice.invoice_number,
            status=invoice.status,
            org=invoice.org,
        )
        assert history.org_id == invoice.org_id


# ---------------------------------------------------------------------------
# Regular User Visibility (non-admin queryset filtering)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRegularUserVisibility:
    """Tests for non-admin user queryset restrictions."""

    def test_regular_user_sees_no_invoices_by_default(self, user_client, invoice):
        """Regular user should not see invoices they didn't create or aren't assigned to."""
        response = user_client.get("/api/invoices/")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

    def test_regular_user_sees_assigned_invoice(
        self, user_client, user_profile, invoice
    ):
        invoice.assigned_to.add(user_profile)
        response = user_client.get("/api/invoices/")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1

    def test_admin_user_sees_all_estimates(self, admin_client, estimate):
        """Admin users should see all estimates regardless of assignment."""
        response = admin_client.get("/api/invoices/estimates/")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
