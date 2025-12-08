from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from accounts.models import Account
from common.base import AssignableMixin, BaseModel
from common.models import Org, Profile, Tags, Teams
from common.utils import CURRENCY_CODES, OPPORTUNITY_TYPES, SOURCES, STAGES
from contacts.models import Contact


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

    def save(self, *args, **kwargs):
        """Auto-set probability based on stage if not manually set."""
        from .workflow import STAGE_PROBABILITIES

        # Auto-set probability based on stage (only if probability is default/0)
        if self.probability == 0 or self.probability is None:
            self.probability = STAGE_PROBABILITIES.get(self.stage, 0)

        super().save(*args, **kwargs)
