"""
Tests for orders/models.py - Order and OrderLineItem models.

Covers:
- Order creation with required fields
- Order __str__ representation
- Order status choices and default
- Order foreign key relationships (account, contact, opportunity)
- Order Meta options (db_table, ordering)
- OrderLineItem creation
- OrderLineItem __str__ representation
- OrderLineItem auto-populate org from parent order
- OrderLineItem Meta options (db_table, ordering)

Run with: pytest orders/tests/test_models.py -v
"""

import uuid
from decimal import Decimal

import pytest

from accounts.models import Account
from contacts.models import Contact
from opportunity.models import Opportunity
from orders.models import ORDER_STATUS, Order, OrderLineItem


# ---------------------------------------------------------------------------
# Order model tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrderModel:
    """Test Order model creation, fields, and behavior."""

    def test_create_order_minimal(self, org_a):
        """Order can be created with just required fields (name, account, org)."""
        account = Account.objects.create(name="Test Account", org=org_a)
        order = Order.objects.create(
            name="Test Order",
            account=account,
            org=org_a,
        )
        assert order.pk is not None
        assert order.name == "Test Order"
        assert order.account == account
        assert order.org == org_a

    def test_str_returns_name(self, org_a):
        """Order __str__ should return the order name."""
        account = Account.objects.create(name="Test Account", org=org_a)
        order = Order.objects.create(
            name="My Sales Order",
            account=account,
            org=org_a,
        )
        assert str(order) == "My Sales Order"

    def test_default_status_is_draft(self, org_a):
        """Order status should default to DRAFT."""
        account = Account.objects.create(name="Test Account", org=org_a)
        order = Order.objects.create(
            name="Test Order",
            account=account,
            org=org_a,
        )
        assert order.status == "DRAFT"

    def test_status_choices(self):
        """ORDER_STATUS should contain expected choices."""
        status_values = [s[0] for s in ORDER_STATUS]
        assert "DRAFT" in status_values
        assert "ACTIVATED" in status_values
        assert "COMPLETED" in status_values
        assert "CANCELLED" in status_values

    def test_create_order_all_fields(self, org_a):
        """Order can be created with all fields populated."""
        account = Account.objects.create(name="Full Account", org=org_a)
        contact = Contact.objects.create(
            first_name="Jane", last_name="Doe", org=org_a
        )
        opportunity = Opportunity.objects.create(
            name="Big Deal",
            account=account,
            org=org_a,
        )
        order = Order.objects.create(
            name="Full Order",
            order_number="ORD-001",
            status="ACTIVATED",
            account=account,
            contact=contact,
            opportunity=opportunity,
            currency="USD",
            subtotal=Decimal("1000.00"),
            discount_amount=Decimal("100.00"),
            tax_amount=Decimal("90.00"),
            total_amount=Decimal("990.00"),
            order_date="2026-01-15",
            activated_date="2026-01-16",
            shipped_date="2026-01-20",
            billing_address_line="123 Main St",
            billing_city="Austin",
            billing_state="TX",
            billing_postcode="78701",
            billing_country="US",
            shipping_address_line="456 Oak Ave",
            shipping_city="Dallas",
            shipping_state="TX",
            shipping_postcode="75201",
            shipping_country="US",
            description="Full order with all fields",
            org=org_a,
        )
        assert order.pk is not None
        assert order.order_number == "ORD-001"
        assert order.status == "ACTIVATED"
        assert order.contact == contact
        assert order.opportunity == opportunity
        assert order.total_amount == Decimal("990.00")
        assert order.billing_city == "Austin"
        assert order.shipping_city == "Dallas"

    def test_order_account_cascade_delete(self, org_a):
        """Deleting an account should cascade-delete its orders."""
        account = Account.objects.create(name="To Delete", org=org_a)
        Order.objects.create(name="Order to Delete", account=account, org=org_a)
        assert Order.objects.count() == 1
        account.delete()
        assert Order.objects.count() == 0

    def test_order_contact_set_null_on_delete(self, org_a):
        """Deleting a contact should set order.contact to NULL."""
        account = Account.objects.create(name="Test Account", org=org_a)
        contact = Contact.objects.create(
            first_name="John", last_name="Doe", org=org_a
        )
        order = Order.objects.create(
            name="Contact Order",
            account=account,
            contact=contact,
            org=org_a,
        )
        contact.delete()
        order.refresh_from_db()
        assert order.contact is None

    def test_order_opportunity_set_null_on_delete(self, org_a):
        """Deleting an opportunity should set order.opportunity to NULL."""
        account = Account.objects.create(name="Test Account", org=org_a)
        opportunity = Opportunity.objects.create(
            name="Opp", account=account, org=org_a
        )
        order = Order.objects.create(
            name="Opp Order",
            account=account,
            opportunity=opportunity,
            org=org_a,
        )
        opportunity.delete()
        order.refresh_from_db()
        assert order.opportunity is None

    def test_order_meta_db_table(self):
        """Order Meta db_table should be 'orders'."""
        assert Order._meta.db_table == "orders"

    def test_order_meta_ordering(self):
        """Order Meta ordering should be ('-created_at',)."""
        assert Order._meta.ordering == ("-created_at",)

    def test_order_decimal_defaults(self, org_a):
        """Financial fields should default to 0."""
        account = Account.objects.create(name="Default Account", org=org_a)
        order = Order.objects.create(name="Default Order", account=account, org=org_a)
        assert order.subtotal == Decimal("0")
        assert order.discount_amount == Decimal("0")
        assert order.tax_amount == Decimal("0")
        assert order.total_amount == Decimal("0")

    def test_order_has_uuid_pk(self, org_a):
        """Order primary key should be a UUID (inherited from BaseOrgModel)."""
        account = Account.objects.create(name="UUID Account", org=org_a)
        order = Order.objects.create(name="UUID Order", account=account, org=org_a)
        assert isinstance(order.pk, uuid.UUID)

    def test_order_has_timestamps(self, org_a):
        """Order should have created_at and updated_at timestamps."""
        account = Account.objects.create(name="Timestamp Account", org=org_a)
        order = Order.objects.create(
            name="Timestamp Order", account=account, org=org_a
        )
        assert order.created_at is not None
        assert order.updated_at is not None


# ---------------------------------------------------------------------------
# OrderLineItem model tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrderLineItemModel:
    """Test OrderLineItem model creation, fields, and behavior."""

    def _make_order(self, org):
        account = Account.objects.create(name="Line Item Account", org=org)
        return Order.objects.create(name="Line Item Order", account=account, org=org)

    def test_create_line_item_minimal(self, org_a):
        """OrderLineItem can be created with required fields."""
        order = self._make_order(org_a)
        item = OrderLineItem.objects.create(
            order=order,
            name="Widget",
            org=org_a,
        )
        assert item.pk is not None
        assert item.name == "Widget"
        assert item.order == order

    def test_str_returns_name(self, org_a):
        """OrderLineItem __str__ should return the item name."""
        order = self._make_order(org_a)
        item = OrderLineItem.objects.create(
            order=order,
            name="Premium Widget",
            org=org_a,
        )
        assert str(item) == "Premium Widget"

    def test_auto_populate_org_from_order(self, org_a):
        """OrderLineItem should inherit org from parent order if not set."""
        order = self._make_order(org_a)
        item = OrderLineItem(order=order, name="Auto Org Item")
        item.save()
        assert item.org_id == org_a.pk

    def test_cross_org_raises_error(self, org_a, org_b):
        """OrderLineItem with org different from order.org should raise ValueError."""
        order = self._make_order(org_a)
        item = OrderLineItem(order=order, name="Cross Org Item", org=org_b)
        with pytest.raises(ValueError, match="must match"):
            item.save()

    def test_line_item_all_fields(self, org_a):
        """OrderLineItem can be created with all fields populated."""
        order = self._make_order(org_a)
        item = OrderLineItem.objects.create(
            order=order,
            name="Full Item",
            description="A fully specified line item",
            quantity=Decimal("5.00"),
            unit_price=Decimal("25.50"),
            discount_amount=Decimal("10.00"),
            sort_order=1,
            org=org_a,
        )
        assert item.quantity == Decimal("5.00")
        assert item.unit_price == Decimal("25.50")
        assert item.discount_amount == Decimal("10.00")
        # total is computed: 5 * 25.50 - 10 = 117.50
        assert item.total == Decimal("117.50")
        assert item.sort_order == 1

    def test_line_item_cascade_delete_with_order(self, org_a):
        """Deleting an order should cascade-delete its line items."""
        order = self._make_order(org_a)
        OrderLineItem.objects.create(order=order, name="Item 1", org=org_a)
        OrderLineItem.objects.create(order=order, name="Item 2", org=org_a)
        assert OrderLineItem.objects.count() == 2
        order.delete()
        assert OrderLineItem.objects.count() == 0

    def test_line_item_product_set_null_on_delete(self, org_a):
        """Deleting a product should set line_item.product to NULL."""
        from invoices.models import Product

        order = self._make_order(org_a)
        product = Product.objects.create(name="Test Product", price=10, org=org_a)
        item = OrderLineItem.objects.create(
            order=order,
            name="Product Item",
            product=product,
            org=org_a,
        )
        product.delete()
        item.refresh_from_db()
        assert item.product is None

    def test_line_item_meta_db_table(self):
        """OrderLineItem Meta db_table should be 'order_line_item'."""
        assert OrderLineItem._meta.db_table == "order_line_item"

    def test_line_item_meta_ordering(self):
        """OrderLineItem Meta ordering should be ('sort_order',)."""
        assert OrderLineItem._meta.ordering == ("sort_order",)

    def test_line_item_decimal_defaults(self, org_a):
        """Financial fields should default to expected values."""
        order = self._make_order(org_a)
        item = OrderLineItem.objects.create(
            order=order, name="Default Item", org=org_a
        )
        assert item.quantity == Decimal("1")
        assert item.unit_price == Decimal("0")
        assert item.discount_amount == Decimal("0")
        # total computed: 1 * 0 - 0 = 0
        assert item.total == Decimal("0")
        assert item.sort_order == 0

    def test_line_item_ordering_by_sort_order(self, org_a):
        """Line items should be ordered by sort_order."""
        order = self._make_order(org_a)
        item_c = OrderLineItem.objects.create(
            order=order, name="C", sort_order=3, org=org_a
        )
        item_a = OrderLineItem.objects.create(
            order=order, name="A", sort_order=1, org=org_a
        )
        item_b = OrderLineItem.objects.create(
            order=order, name="B", sort_order=2, org=org_a
        )
        items = list(OrderLineItem.objects.all())
        assert items == [item_a, item_b, item_c]

    def test_order_line_items_related_name(self, org_a):
        """Order.line_items should return associated OrderLineItems."""
        order = self._make_order(org_a)
        OrderLineItem.objects.create(order=order, name="Item 1", org=org_a)
        OrderLineItem.objects.create(order=order, name="Item 2", org=org_a)
        assert order.line_items.count() == 2
