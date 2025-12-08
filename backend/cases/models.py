from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from accounts.models import Account
from common.base import AssignableMixin, BaseModel
from common.models import Org, Profile, Tags, Teams
from common.utils import CASE_TYPE, PRIORITY_CHOICE, STATUS_CHOICE
from contacts.models import Contact


# Cleanup notes:
# - Removed 'created_on_arrow' property from Case and Solution (frontend computes its own timestamps)
# - Fixed case_type default from "" to None (empty string is bad default for nullable field)


class Case(AssignableMixin, BaseModel):
    name = models.CharField(pgettext_lazy("Name of the case", "Name"), max_length=64)
    status = models.CharField(choices=STATUS_CHOICE, max_length=64)
    priority = models.CharField(choices=PRIORITY_CHOICE, max_length=64)
    case_type = models.CharField(
        choices=CASE_TYPE, max_length=255, blank=True, null=True, default=None
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="accounts_cases",
    )
    contacts = models.ManyToManyField(Contact, related_name="case_contacts")
    closed_on = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.ManyToManyField(Profile, related_name="case_assigned_users")
    is_active = models.BooleanField(default=True)
    teams = models.ManyToManyField(Teams, related_name="cases_teams")
    tags = models.ManyToManyField(Tags, related_name="case_tags", blank=True)
    org = models.ForeignKey(Org, on_delete=models.CASCADE, related_name="cases")

    # SLA Tracking Fields
    first_response_at = models.DateTimeField(
        _("First Response At"), blank=True, null=True
    )
    resolved_at = models.DateTimeField(_("Resolved At"), blank=True, null=True)
    sla_first_response_hours = models.PositiveIntegerField(
        _("First Response SLA (hours)"),
        default=4,
        help_text="Target hours for first response",
    )
    sla_resolution_hours = models.PositiveIntegerField(
        _("Resolution SLA (hours)"),
        default=24,
        help_text="Target hours for resolution",
    )

    class Meta:
        verbose_name = "Case"
        verbose_name_plural = "Cases"
        db_table = "case"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["org", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.name}"

    def clean(self):
        """Validate case data."""
        super().clean()
        errors = {}

        # Closed date required when status is Closed
        if self.status == "Closed" and not self.closed_on:
            errors["closed_on"] = _("Closed date is required when closing a case")

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Auto-set SLA values based on priority for new cases."""
        from .workflow import DEFAULT_FIRST_RESPONSE_SLA, DEFAULT_RESOLUTION_SLA

        # Set default SLA based on priority for new cases
        if not self.pk:
            if self.sla_first_response_hours == 4:  # Default value
                self.sla_first_response_hours = DEFAULT_FIRST_RESPONSE_SLA.get(
                    self.priority, 4
                )
            if self.sla_resolution_hours == 24:  # Default value
                self.sla_resolution_hours = DEFAULT_RESOLUTION_SLA.get(
                    self.priority, 24
                )

        super().save(*args, **kwargs)

    @property
    def is_sla_first_response_breached(self) -> bool:
        """Check if first response SLA has been breached."""
        if self.first_response_at:
            return False
        if not self.created_at:
            return False
        deadline = self.created_at + timedelta(hours=self.sla_first_response_hours)
        return timezone.now() > deadline

    @property
    def is_sla_resolution_breached(self) -> bool:
        """Check if resolution SLA has been breached."""
        if self.resolved_at:
            return False
        if not self.created_at:
            return False
        deadline = self.created_at + timedelta(hours=self.sla_resolution_hours)
        return timezone.now() > deadline

    @property
    def first_response_sla_deadline(self):
        """Return the deadline for first response."""
        if self.created_at:
            return self.created_at + timedelta(hours=self.sla_first_response_hours)
        return None

    @property
    def resolution_sla_deadline(self):
        """Return the deadline for resolution."""
        if self.created_at:
            return self.created_at + timedelta(hours=self.sla_resolution_hours)
        return None


class Solution(BaseModel):
    """
    Knowledge Base Solution

    Solutions are reusable answers/guides that can be linked to cases.
    They form a knowledge base for common issues and their resolutions.
    """

    title = models.CharField(max_length=255)
    description = models.TextField()

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("reviewed", "Reviewed"),
        ("approved", "Approved"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    is_published = models.BooleanField(default=False)

    # Organization relation
    org = models.ForeignKey(Org, on_delete=models.CASCADE, related_name="solutions")

    # Cases that use this solution
    cases = models.ManyToManyField(Case, related_name="solutions", blank=True)

    class Meta:
        verbose_name = "Solution"
        verbose_name_plural = "Solutions"
        db_table = "solution"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["is_published"]),
            models.Index(fields=["org"]),
        ]

    def __str__(self):
        return self.title

    def publish(self):
        """Publish the solution (must be approved first)"""
        if self.status == "approved":
            self.is_published = True
            self.save()

    def unpublish(self):
        """Unpublish the solution"""
        self.is_published = False
        self.save()
