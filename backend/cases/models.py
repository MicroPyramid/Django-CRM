import arrow
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from accounts.models import Account
from common.base import AssignableMixin, BaseModel
from common.models import Org, Profile, Tags, Teams
from common.utils import CASE_TYPE, PRIORITY_CHOICE, STATUS_CHOICE
from contacts.models import Contact


class Case(AssignableMixin, BaseModel):
    name = models.CharField(pgettext_lazy("Name of the case", "Name"), max_length=64)
    status = models.CharField(choices=STATUS_CHOICE, max_length=64)
    priority = models.CharField(choices=PRIORITY_CHOICE, max_length=64)
    case_type = models.CharField(
        choices=CASE_TYPE, max_length=255, blank=True, null=True, default=""
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="accounts_cases",
    )
    contacts = models.ManyToManyField(Contact, related_name="case_contacts")
    # closed_on = models.DateTimeField()
    closed_on = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.ManyToManyField(Profile, related_name="case_assigned_users")
    # created_by = models.ForeignKey(
    #     Profile, related_name="case_created_by", on_delete=models.SET_NULL, null=True
    # )
    is_active = models.BooleanField(default=True)
    teams = models.ManyToManyField(Teams, related_name="cases_teams")
    tags = models.ManyToManyField(Tags, blank=True)
    org = models.ForeignKey(Org, on_delete=models.CASCADE, related_name="cases")

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

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_at).humanize()


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

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_at).humanize()
