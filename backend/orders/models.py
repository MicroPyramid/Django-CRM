from django.db import models
from django.utils.translation import gettext_lazy as _

from common.base import BaseOrgModel
from common.utils import COUNTRIES


# =============================================================================
# CONSTANTS
# =============================================================================

ORDER_STATUS = (
    ("DRAFT", "Draft"),
    ("ACTIVATED", "Activated"),
    ("COMPLETED", "Completed"),
    ("CANCELLED", "Cancelled"),
)


# =============================================================================
# ORDER
# =============================================================================


class Order(BaseOrgModel):
    """
    Order model for CRM - tracks sales orders linked to accounts,
    contacts, and opportunities.
    """

    # Core Order Information
    name = models.CharField(_("Order Name"), max_length=255)
    order_number = models.CharField(
        _("Order Number"), max_length=100, blank=True, null=True
    )
    status = models.CharField(
        _("Status"), max_length=20, choices=ORDER_STATUS, default="DRAFT"
    )

    # CRM Integration
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="orders",
        help_text="The account this order belongs to",
    )
    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
        blank=True,
        help_text="The contact associated with this order",
    )
    opportunity = models.ForeignKey(
        "opportunity.Opportunity",
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
        blank=True,
        help_text="The opportunity this order originated from",
    )

    # Financial
    currency = models.CharField(_("Currency"), max_length=3, blank=True, null=True)
    subtotal = models.DecimalField(
        _("Subtotal"), max_digits=15, decimal_places=2, default=0
    )
    discount_amount = models.DecimalField(
        _("Discount Amount"), max_digits=15, decimal_places=2, default=0
    )
    tax_amount = models.DecimalField(
        _("Tax Amount"), max_digits=15, decimal_places=2, default=0
    )
    total_amount = models.DecimalField(
        _("Total Amount"), max_digits=15, decimal_places=2, default=0
    )

    # Dates
    order_date = models.DateField(_("Order Date"), null=True, blank=True)
    activated_date = models.DateField(_("Activated Date"), null=True, blank=True)
    shipped_date = models.DateField(_("Shipped Date"), null=True, blank=True)

    # Billing Address
    billing_address_line = models.CharField(
        _("Billing Address"), max_length=255, blank=True, null=True
    )
    billing_city = models.CharField(
        _("Billing City"), max_length=100, blank=True, null=True
    )
    billing_state = models.CharField(
        _("Billing State"), max_length=100, blank=True, null=True
    )
    billing_postcode = models.CharField(
        _("Billing Postal Code"), max_length=20, blank=True, null=True
    )
    billing_country = models.CharField(
        _("Billing Country"), max_length=3, choices=COUNTRIES, blank=True, null=True
    )

    # Shipping Address
    shipping_address_line = models.CharField(
        _("Shipping Address"), max_length=255, blank=True, null=True
    )
    shipping_city = models.CharField(
        _("Shipping City"), max_length=100, blank=True, null=True
    )
    shipping_state = models.CharField(
        _("Shipping State"), max_length=100, blank=True, null=True
    )
    shipping_postcode = models.CharField(
        _("Shipping Postal Code"), max_length=20, blank=True, null=True
    )
    shipping_country = models.CharField(
        _("Shipping Country"), max_length=3, choices=COUNTRIES, blank=True, null=True
    )

    # Notes
    description = models.TextField(_("Description"), blank=True, null=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        db_table = "orders"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["org", "-created_at"]),
        ]

    def __str__(self):
        return self.name


# =============================================================================
# ORDER LINE ITEM
# =============================================================================


class OrderLineItem(BaseOrgModel):
    """Line item for Orders - individual products/services within an order."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="line_items"
    )
    product = models.ForeignKey(
        "invoices.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_line_items",
    )
    name = models.CharField(_("Item Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True, null=True)
    quantity = models.DecimalField(
        _("Quantity"), max_digits=10, decimal_places=2, default=1
    )
    unit_price = models.DecimalField(
        _("Unit Price"), max_digits=15, decimal_places=2, default=0
    )
    discount_amount = models.DecimalField(
        _("Discount Amount"), max_digits=15, decimal_places=2, default=0
    )
    total = models.DecimalField(_("Total"), max_digits=15, decimal_places=2, default=0)
    sort_order = models.IntegerField(_("Sort Order"), default=0)

    class Meta:
        verbose_name = "Order Line Item"
        verbose_name_plural = "Order Line Items"
        db_table = "order_line_item"
        ordering = ("sort_order",)
        indexes = [
            models.Index(fields=["org", "-created_at"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Inherit org from order if not set
        if not self.org_id and self.order_id:
            self.org_id = self.order.org_id
        super().save(*args, **kwargs)
