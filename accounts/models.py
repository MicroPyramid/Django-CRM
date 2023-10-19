import arrow
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from phonenumber_field.modelfields import PhoneNumberField

from common import utils
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

    ACCOUNT_STATUS_CHOICE = (("open", "Open"), ("close", "Close"))

    name = models.CharField(pgettext_lazy("Name of Account", "Name"), max_length=64)
    email = models.EmailField()
    phone = PhoneNumberField(null=True)
    industry = models.CharField(
        _("Industry Type"), max_length=255, choices=INDCHOICES, blank=True, null=True
    )
    # billing_address = models.ForeignKey(
    #     Address, related_name='account_billing_address', on_delete=models.CASCADE, blank=True, null=True)
    # shipping_address = models.ForeignKey(
    #     Address, related_name='account_shipping_address', on_delete=models.CASCADE, blank=True, null=True)
    billing_address_line = models.CharField(
        _("Address"), max_length=255, blank=True, null=True
    )
    billing_street = models.CharField(_("Street"), max_length=55, blank=True, null=True)
    billing_city = models.CharField(_("City"), max_length=255, blank=True, null=True)
    billing_state = models.CharField(_("State"), max_length=255, blank=True, null=True)
    billing_postcode = models.CharField(
        _("Post/Zip-code"), max_length=64, blank=True, null=True
    )
    billing_country = models.CharField(
        max_length=3, choices=COUNTRIES, blank=True, null=True
    )
    website = models.URLField(_("Website"), blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    # created_by = models.ForeignKey(
    #     Profile, related_name="account_created_by", on_delete=models.SET_NULL, null=True
    # )
    is_active = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tags, blank=True)
    status = models.CharField(
        choices=ACCOUNT_STATUS_CHOICE, max_length=64, default="open"
    )
    lead = models.ForeignKey(
        "leads.Lead", related_name="account_leads", on_delete=models.SET_NULL, null=True
    )
    contact_name = models.CharField(
        pgettext_lazy("Name of Contact", "Contact Name"), max_length=120
    )
    contacts = models.ManyToManyField(
        "contacts.Contact", related_name="account_contacts"
    )
    assigned_to = models.ManyToManyField(Profile, related_name="account_assigned_users")
    teams = models.ManyToManyField(Teams, related_name="account_teams")
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
        address = ""
        add_to_address = [
            self.billing_street,
            self.billing_city,
            self.billing_state,
            self.billing_postcode,
            self.get_billing_country_display(),
        ]
        address = utils.append_str_to(address, *add_to_address)

        return address

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
