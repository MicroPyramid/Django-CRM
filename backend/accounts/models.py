import arrow
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from phonenumber_field.modelfields import PhoneNumberField

from common.models import Org, Profile
from common.utils import COUNTRIES, INDCHOICES
from contacts.models import Contact
from teams.models import Teams
from common.base import BaseModel


class Tags(BaseModel):
    name = models.CharField(max_length=20)
    slug = models.CharField(max_length=20, unique=True, blank=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        db_table = "tags"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Account(BaseModel):
    """
    Account model for CRM - Streamlined for modern sales workflow
    Based on Twenty CRM and Salesforce patterns
    """
    # Core Account Information
    name = models.CharField(_("Account Name"), max_length=255)
    email = models.EmailField(_("Email"), blank=True, null=True)
    phone = PhoneNumberField(_("Phone"), null=True, blank=True)
    website = models.URLField(_("Website"), blank=True, null=True)

    # Business Information
    industry = models.CharField(
        _("Industry"), max_length=255, choices=INDCHOICES, blank=True, null=True
    )
    number_of_employees = models.PositiveIntegerField(
        _("Number of Employees"), blank=True, null=True
    )
    annual_revenue = models.DecimalField(
        _("Annual Revenue"), max_digits=15, decimal_places=2, blank=True, null=True
    )

    # Address (flat fields like Lead and Contact models)
    address_line = models.CharField(_("Address"), max_length=255, blank=True, null=True)
    city = models.CharField(_("City"), max_length=255, blank=True, null=True)
    state = models.CharField(_("State"), max_length=255, blank=True, null=True)
    postcode = models.CharField(_("Postal Code"), max_length=64, blank=True, null=True)
    country = models.CharField(
        _("Country"), max_length=3, choices=COUNTRIES, blank=True, null=True
    )

    # Assignment
    assigned_to = models.ManyToManyField(Profile, related_name="account_assigned_users")
    teams = models.ManyToManyField(Teams, related_name="account_teams")
    contacts = models.ManyToManyField(
        "contacts.Contact", related_name="account_contacts"
    )

    # Tags
    tags = models.ManyToManyField(Tags, blank=True)

    # Notes
    description = models.TextField(_("Notes"), blank=True, null=True)

    # System Fields
    is_active = models.BooleanField(default=False)
    org = models.ForeignKey(
        Org,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="account_org",
    )

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        db_table = "accounts"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name}"

    def get_complete_address(self):
        """Concatenates complete address."""
        address_parts = [
            self.address_line,
            self.city,
            self.state,
            self.postcode,
            self.get_country_display() if self.country else None,
        ]
        return ", ".join(part for part in address_parts if part)

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_at).humanize()

    @property
    def contact_values(self):
        contacts = list(self.contacts.values_list("id", flat=True))
        return ",".join(str(contact) for contact in contacts)

    @property
    def get_team_users(self):
        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        return Profile.objects.filter(id__in=team_user_ids)

    @property
    def get_team_and_assigned_users(self):
        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        assigned_user_ids = list(self.assigned_to.values_list("id", flat=True))
        user_ids = team_user_ids + assigned_user_ids
        return Profile.objects.filter(id__in=user_ids)

    @property
    def get_assigned_users_not_in_teams(self):
        team_user_ids = list(self.teams.values_list("users__id", flat=True))
        assigned_user_ids = list(self.assigned_to.values_list("id", flat=True))
        user_ids = set(assigned_user_ids) - set(team_user_ids)
        return Profile.objects.filter(id__in=list(user_ids))


class AccountEmail(BaseModel):
    from_account = models.ForeignKey(
        Account, related_name="sent_email", on_delete=models.SET_NULL, null=True
    )
    recipients = models.ManyToManyField(Contact, related_name="recieved_email")
    message_subject = models.TextField(null=True)
    message_body = models.TextField(null=True)
    timezone = models.CharField(max_length=100, default="UTC")
    scheduled_date_time = models.DateTimeField(null=True)
    scheduled_later = models.BooleanField(default=False)
    from_email = models.EmailField()
    rendered_message_body = models.TextField(null=True)

    class Meta:
        verbose_name = "Account Email"
        verbose_name_plural = "Account Emails"
        db_table = "account_email"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.message_subject}"

class AccountEmailLog(BaseModel):
    """this model is used to track if the email is sent or not"""

    email = models.ForeignKey(
        AccountEmail, related_name="email_log", on_delete=models.SET_NULL, null=True
    )
    contact = models.ForeignKey(
        Contact, related_name="contact_email_log", on_delete=models.SET_NULL, null=True
    )
    is_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "EmailLog"
        verbose_name_plural = "EmailLogs"
        db_table = "emailLogs"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.email.message_subject}"
