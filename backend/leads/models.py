from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.base import AssignableMixin, BaseModel
from common.models import Org, Profile, Tags, Teams
from common.utils import (
    COUNTRIES,
    CURRENCY_CODES,
    INDCHOICES,
    LEAD_SOURCE,
    LEAD_STATUS,
)
from common.validators import flexible_phone_validator
from contacts.models import Contact


# Cleanup notes:
# - Removed 'created_from_site' flag (over-engineered)
# - Removed conversion tracking fields (converted_account, converted_contact,
#   converted_opportunity, conversion_date) - never populated, conversion just sets status
# - Removed 'created_on_arrow' property (frontend computes its own timestamps)


class Lead(AssignableMixin, BaseModel):
    """
    Lead model for CRM - Streamlined for modern sales workflow
    Based on Twenty CRM and Salesforce patterns
    """

    # Core Lead Information
    title = models.CharField(
        _("Title"), max_length=255, blank=True, null=True,
        help_text="Lead name/subject (e.g., 'Enterprise Deal', 'Website Inquiry')"
    )
    salutation = models.CharField(
        _("Salutation"), max_length=64, blank=True, null=True,
        help_text="e.g., Mr, Mrs, Ms, Dr"
    )
    first_name = models.CharField(_("First name"), null=True, max_length=255)
    last_name = models.CharField(_("Last name"), null=True, max_length=255)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(
        _("Phone"),
        max_length=25,
        null=True,
        blank=True,
        validators=[flexible_phone_validator],
    )
    job_title = models.CharField(
        _("Job Title"), max_length=255, blank=True, null=True,
        help_text="Person's job title (e.g., 'VP of Sales', 'CTO')"
    )
    website = models.CharField(_("Website"), max_length=255, blank=True, null=True)
    linkedin_url = models.URLField(
        _("LinkedIn URL"), max_length=500, blank=True, null=True
    )

    # Sales Pipeline
    status = models.CharField(
        _("Status"), max_length=255, blank=True, null=True, choices=LEAD_STATUS
    )
    source = models.CharField(
        _("Source"), max_length=255, blank=True, null=True, choices=LEAD_SOURCE
    )
    industry = models.CharField(
        _("Industry"), max_length=255, choices=INDCHOICES, blank=True, null=True
    )
    rating = models.CharField(
        _("Rating"),
        max_length=10,
        blank=True,
        null=True,
        choices=[("HOT", "Hot"), ("WARM", "Warm"), ("COLD", "Cold")],
    )
    opportunity_amount = models.DecimalField(
        _("Deal Value"), decimal_places=2, max_digits=12, blank=True, null=True
    )
    currency = models.CharField(
        _("Currency"), max_length=3, choices=CURRENCY_CODES, blank=True, null=True
    )
    probability = models.IntegerField(
        _("Win Probability %"), default=0, blank=True, null=True
    )
    close_date = models.DateField(_("Expected Close Date"), default=None, null=True)

    # Address
    address_line = models.CharField(_("Address"), max_length=255, blank=True, null=True)
    city = models.CharField(_("City"), max_length=255, blank=True, null=True)
    state = models.CharField(_("State"), max_length=255, blank=True, null=True)
    postcode = models.CharField(_("Postal Code"), max_length=64, blank=True, null=True)
    country = models.CharField(
        _("Country"), max_length=3, choices=COUNTRIES, blank=True, null=True
    )

    # Assignment
    assigned_to = models.ManyToManyField(Profile, related_name="lead_assigned_users")
    teams = models.ManyToManyField(Teams, related_name="lead_teams")

    # Activity Tracking
    last_contacted = models.DateField(_("Last Contacted"), blank=True, null=True)
    next_follow_up = models.DateField(_("Next Follow-up"), blank=True, null=True)
    description = models.TextField(_("Notes"), blank=True, null=True)

    # System Fields
    is_active = models.BooleanField(default=True)
    tags = models.ManyToManyField(Tags, related_name="lead_tags", blank=True)
    contacts = models.ManyToManyField(Contact, related_name="lead_contacts")
    org = models.ForeignKey(Org, on_delete=models.CASCADE, related_name="leads")
    company_name = models.CharField(
        _("Company Name"), max_length=255, blank=True, null=True
    )

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        db_table = "lead"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["source"]),
            models.Index(fields=["org", "-created_at"]),
        ]
        constraints = [
            # Case-insensitive unique email per organization (when email is not null)
            models.UniqueConstraint(
                Lower("email"),
                "org",
                name="unique_lead_email_per_org",
                condition=Q(email__isnull=False) & ~Q(email=""),
            ),
            # Probability must be 0-100
            models.CheckConstraint(
                check=Q(probability__gte=0) & Q(probability__lte=100),
                name="lead_probability_range",
            ),
            # Opportunity amount must be non-negative
            models.CheckConstraint(
                check=Q(opportunity_amount__gte=0) | Q(opportunity_amount__isnull=True),
                name="lead_amount_non_negative",
            ),
        ]

    def __str__(self):
        name_parts = [self.salutation, self.first_name, self.last_name]
        return " ".join(part for part in name_parts if part) or f"Lead {self.id}"

    def clean(self):
        """Validate lead data."""
        super().clean()
        errors = {}

        # Email required for conversion (need contact info to create Contact)
        if self.status == "converted" and not self.email:
            errors["email"] = _("Email is required to convert lead")

        if errors:
            raise ValidationError(errors)

    @property
    def days_since_last_contact(self) -> int:
        """Return the number of days since last contact or creation."""
        if self.last_contacted:
            return (timezone.now().date() - self.last_contacted).days
        if self.created_at:
            return (timezone.now().date() - self.created_at.date()).days
        return 0

    @property
    def is_stale(self) -> bool:
        """Check if lead is stale (>30 days without contact and not closed/converted)."""
        if self.status in ["converted", "closed"]:
            return False
        return self.days_since_last_contact > 30

    @property
    def days_until_follow_up(self) -> int | None:
        """Return the number of days until next follow-up (negative if overdue)."""
        if not self.next_follow_up:
            return None
        return (self.next_follow_up - timezone.now().date()).days

    @property
    def is_follow_up_overdue(self) -> bool:
        """Check if follow-up date has passed."""
        if not self.next_follow_up:
            return False
        return timezone.now().date() > self.next_follow_up

