import arrow
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from common.base import AssignableMixin, BaseModel
from common.models import Org, Profile, Tags, Teams
from common.utils import COUNTRIES


class Contact(AssignableMixin, BaseModel):
    """
    Contact model for CRM - Streamlined for modern sales workflow
    Based on Twenty CRM and Salesforce patterns
    """

    # Core Contact Information
    first_name = models.CharField(_("First name"), max_length=255)
    last_name = models.CharField(_("Last name"), max_length=255)
    email = models.EmailField(_("Email"), blank=True, null=True)
    phone = PhoneNumberField(_("Phone"), null=True, blank=True)

    # Professional Information
    organization = models.CharField(_("Company"), max_length=255, blank=True, null=True)
    title = models.CharField(_("Job Title"), max_length=255, blank=True, null=True)
    department = models.CharField(
        _("Department"), max_length=255, blank=True, null=True
    )

    # Communication Preferences
    do_not_call = models.BooleanField(_("Do Not Call"), default=False)
    linkedin_url = models.URLField(_("LinkedIn URL"), blank=True, null=True)

    # Address (flat fields like Lead model)
    address_line = models.CharField(_("Address"), max_length=255, blank=True, null=True)
    city = models.CharField(_("City"), max_length=255, blank=True, null=True)
    state = models.CharField(_("State"), max_length=255, blank=True, null=True)
    postcode = models.CharField(_("Postal Code"), max_length=64, blank=True, null=True)
    country = models.CharField(
        _("Country"), max_length=3, choices=COUNTRIES, blank=True, null=True
    )

    # Assignment
    assigned_to = models.ManyToManyField(Profile, related_name="contact_assigned_users")
    teams = models.ManyToManyField(Teams, related_name="contact_teams")

    # Tags
    tags = models.ManyToManyField(Tags, blank=True)

    # Notes
    description = models.TextField(_("Notes"), blank=True, null=True)

    # System Fields
    is_active = models.BooleanField(default=True)
    org = models.ForeignKey(Org, on_delete=models.CASCADE, related_name="contacts")

    # Account relationship (optional - contact can exist without an account)
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_contacts",
        help_text="Primary account this contact belongs to",
    )

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        db_table = "contacts"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["organization"]),
            models.Index(fields=["org", "-created_at"]),
        ]

    def __str__(self):
        return self.first_name

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_at).humanize()

    @property
    def created_on(self):
        return self.created_at
