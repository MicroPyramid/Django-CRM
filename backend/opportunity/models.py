from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from accounts.models import Account
from common.base import AssignableMixin, BaseModel
from common.models import Org, Profile, Tags, Teams
from common.utils import CURRENCY_CODES, OPPORTUNITY_TYPES, SOURCES, STAGES
from contacts.models import Contact


# Amount source choices for Opportunity
AMOUNT_SOURCE_CHOICES = (
    ("MANUAL", "Manual"),
    ("CALCULATED", "Calculated from Products"),
)

# Discount type choices
DISCOUNT_TYPES = (
    ("PERCENTAGE", "Percentage (%)"),
    ("FIXED", "Fixed Amount"),
)


class Opportunity(AssignableMixin, BaseModel):
    """
    Opportunity model for CRM - Sales pipeline management
    Based on Twenty CRM and Salesforce patterns
    """

    # Core Opportunity Information
    name = models.CharField(_("Opportunity Name"), max_length=255)
    account = models.ForeignKey(
        Account,
        related_name="opportunities",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    stage = models.CharField(
        _("Stage"), max_length=64, choices=STAGES, default="PROSPECTING"
    )
    opportunity_type = models.CharField(
        _("Type"), max_length=64, choices=OPPORTUNITY_TYPES, blank=True, null=True
    )

    # Financial Information
    currency = models.CharField(
        _("Currency"), max_length=3, choices=CURRENCY_CODES, blank=True, null=True
    )
    amount = models.DecimalField(
        _("Amount"), decimal_places=2, max_digits=12, blank=True, null=True
    )
    amount_source = models.CharField(
        _("Amount Source"),
        max_length=20,
        choices=AMOUNT_SOURCE_CHOICES,
        default="MANUAL",
    )
    probability = models.IntegerField(
        _("Probability (%)"), default=0, blank=True, null=True
    )
    closed_on = models.DateField(_("Expected Close Date"), blank=True, null=True)

    # Source & Context
    lead_source = models.CharField(
        _("Lead Source"), max_length=255, choices=SOURCES, blank=True, null=True
    )

    # Relationships
    contacts = models.ManyToManyField(Contact, related_name="opportunity_contacts")

    # Assignment
    assigned_to = models.ManyToManyField(
        Profile, related_name="opportunity_assigned_users"
    )
    teams = models.ManyToManyField(Teams, related_name="opportunity_teams")
    closed_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opportunity_closed_by",
    )

    # Tags
    tags = models.ManyToManyField(Tags, related_name="opportunity_tags", blank=True)

    # Notes
    description = models.TextField(_("Notes"), blank=True, null=True)

    # System Fields
    is_active = models.BooleanField(default=True)
    org = models.ForeignKey(
        Org,
        on_delete=models.CASCADE,
        related_name="opportunities",
    )

    class Meta:
        verbose_name = "Opportunity"
        verbose_name_plural = "Opportunities"
        db_table = "opportunity"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["stage"]),
            models.Index(fields=["org", "-created_at"]),
        ]
        constraints = [
            # Probability must be 0-100
            models.CheckConstraint(
                check=Q(probability__gte=0) & Q(probability__lte=100),
                name="opportunity_probability_range",
            ),
            # Amount must be non-negative
            models.CheckConstraint(
                check=Q(amount__gte=0) | Q(amount__isnull=True),
                name="opportunity_amount_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.name}"

    @property
    def created_on_arrow(self):
        return timesince(self.created_at) + " ago"

    def clean(self):
        """Validate opportunity data."""
        super().clean()
        errors = {}

        # Closed date required for closed stages
        if self.stage in ["CLOSED_WON", "CLOSED_LOST"] and not self.closed_on:
            errors["closed_on"] = _(
                "Close date is required when stage is Closed Won/Lost"
            )

        # Amount required for closed won
        if self.stage == "CLOSED_WON" and not self.amount:
            errors["amount"] = _("Amount is required for Closed Won opportunities")

        if errors:
            raise ValidationError(errors)

    def recalculate_amount(self):
        """
        Recalculate opportunity amount from line items.
        Only updates if amount_source is CALCULATED or if line items exist.
        Returns True if amount was updated, False otherwise.
        """
        line_items = self.line_items.all()
        if line_items.exists():
            total = line_items.aggregate(total=Sum("total"))["total"] or Decimal("0")
            self.amount = total
            self.amount_source = "CALCULATED"
            return True
        elif self.amount_source == "CALCULATED":
            # No line items but was calculated - reset to manual
            self.amount_source = "MANUAL"
            self.amount = Decimal("0")
            return True
        return False

    def save(self, *args, **kwargs):
        """Auto-set probability based on stage if not manually set."""
        from .workflow import STAGE_PROBABILITIES

        # Auto-set probability based on stage (only if probability is default/0)
        if self.probability == 0 or self.probability is None:
            self.probability = STAGE_PROBABILITIES.get(self.stage, 0)

        super().save(*args, **kwargs)


class OpportunityLineItem(BaseModel):
    """
    Line item for an opportunity - represents a product or service being quoted.
    Similar to InvoiceLineItem but for the pre-sale stage.
    """

    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name="line_items",
    )
    product = models.ForeignKey(
        "invoices.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opportunity_line_items",
    )

    # Item details (can override product info or be custom)
    name = models.CharField(_("Item Name"), max_length=255, blank=True)
    description = models.CharField(_("Description"), max_length=500, blank=True)

    # Quantity and pricing
    quantity = models.DecimalField(
        _("Quantity"), max_digits=10, decimal_places=2, default=1
    )
    unit_price = models.DecimalField(
        _("Unit Price"), max_digits=12, decimal_places=2, default=0
    )

    # Per-item discount
    discount_type = models.CharField(
        _("Discount Type"), max_length=20, choices=DISCOUNT_TYPES, blank=True
    )
    discount_value = models.DecimalField(
        _("Discount Value"), max_digits=12, decimal_places=2, default=0
    )
    discount_amount = models.DecimalField(
        _("Discount Amount"), max_digits=12, decimal_places=2, default=0
    )

    # Computed totals
    subtotal = models.DecimalField(
        _("Subtotal"), max_digits=12, decimal_places=2, default=0
    )
    total = models.DecimalField(_("Total"), max_digits=12, decimal_places=2, default=0)

    # Display order
    order = models.PositiveIntegerField(_("Order"), default=0)

    # Organization (for RLS)
    org = models.ForeignKey(
        Org,
        on_delete=models.CASCADE,
        related_name="opportunity_line_items",
    )

    class Meta:
        verbose_name = "Opportunity Line Item"
        verbose_name_plural = "Opportunity Line Items"
        db_table = "opportunity_line_item"
        ordering = ["order", "created_at"]
        indexes = [
            models.Index(fields=["opportunity"]),
            models.Index(fields=["org"]),
        ]

    def __str__(self):
        return f"{self.name or self.product.name if self.product else 'Item'} x {self.quantity}"

    def save(self, *args, **kwargs):
        """Calculate totals before saving."""
        # Get name from product if not set
        if not self.name and self.product:
            self.name = self.product.name

        # Get unit price from product if not set and product exists
        if self.unit_price == 0 and self.product:
            self.unit_price = self.product.price or Decimal("0")

        # Calculate subtotal
        self.subtotal = self.quantity * self.unit_price

        # Calculate discount
        if self.discount_type == "PERCENTAGE":
            self.discount_amount = self.subtotal * (
                self.discount_value / Decimal("100")
            )
        else:
            self.discount_amount = self.discount_value

        # Calculate total (no tax at opportunity stage)
        self.total = self.subtotal - self.discount_amount

        # Ensure org is set from opportunity if not provided
        if not self.org_id and self.opportunity_id:
            self.org_id = self.opportunity.org_id

        super().save(*args, **kwargs)

        # Recalculate opportunity amount after saving line item
        if self.opportunity:
            self.opportunity.recalculate_amount()
            self.opportunity.save(update_fields=["amount", "amount_source"])

    def delete(self, *args, **kwargs):
        """Recalculate opportunity amount after deleting line item."""
        opportunity = self.opportunity
        super().delete(*args, **kwargs)

        # Recalculate opportunity amount after deletion
        if opportunity:
            opportunity.recalculate_amount()
            opportunity.save(update_fields=["amount", "amount_source"])
