import arrow
from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from accounts.models import Tags
from common.models import User
from common.utils import (COUNTRIES, LEAD_SOURCE, LEAD_STATUS,
                          return_complete_address)
from contacts.models import Contact
from teams.models import Teams

class Lead(models.Model):
    title = models.CharField(
        pgettext_lazy("Treatment Pronouns for the customer",
                      "Title"), max_length=64)
    first_name = models.CharField(_("First name"), null=True, max_length=255)
    last_name = models.CharField(_("Last name"), null=True, max_length=255)
    email = models.EmailField(null=True, blank=True)
    phone = PhoneNumberField(null=True, blank=True)
    status = models.CharField(
        _("Status of Lead"),
        max_length=255, blank=True,
        null=True, choices=LEAD_STATUS)
    source = models.CharField(
        _("Source of Lead"), max_length=255,
        blank=True, null=True, choices=LEAD_SOURCE)
    address_line = models.CharField(
        _("Address"), max_length=255, blank=True, null=True)
    street = models.CharField(
        _("Street"), max_length=55, blank=True, null=True)
    city = models.CharField(_("City"), max_length=255, blank=True, null=True)
    state = models.CharField(_("State"), max_length=255, blank=True, null=True)
    postcode = models.CharField(
        _("Post/Zip-code"), max_length=64, blank=True, null=True)
    country = models.CharField(
        max_length=3, choices=COUNTRIES, blank=True, null=True)
    website = models.CharField(
        _("Website"), max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.ManyToManyField(
        User, related_name='lead_assigned_users')
    account_name = models.CharField(max_length=255, null=True, blank=True)
    opportunity_amount = models.DecimalField(
        _("Opportunity Amount"),
        decimal_places=2, max_digits=12,
        blank=True, null=True)
    created_by = models.ForeignKey(
        User, related_name='lead_created_by',
        on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(_("Created on"), auto_now_add=True)
    is_active = models.BooleanField(default=False)
    enquery_type = models.CharField(max_length=255, blank=True, null=True)
    tags = models.ManyToManyField(Tags, blank=True)
    contacts = models.ManyToManyField(Contact, related_name="lead_contacts")
    created_from_site = models.BooleanField(default=False)
    teams = models.ManyToManyField(Teams, related_name='lead_teams')

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return self.title

    def get_complete_address(self):
        return return_complete_address(self)

    @property
    def phone_raw_input(self):
        if str(self.phone) == '+NoneNone':
            return ''
        return self.phone

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_on).humanize()
