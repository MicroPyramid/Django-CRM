from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from common.models import User
from common.utils import INDCHOICES, COUNTRIES
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.text import slugify


class Tags(models.Model):
    name = models.CharField(max_length=20)
    slug = models.CharField(max_length=20, unique=True, blank=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Tags, self).save(*args, **kwargs)


class Account(models.Model):

    ACCOUNT_STATUS_CHOICE = (
        ("open", "Open"),
        ('close', 'Close')
    )

    name = models.CharField(pgettext_lazy("Name of Account", "Name"), max_length=64)
    email = models.EmailField()
    phone = PhoneNumberField(null=True)
    industry = models.CharField(_("Industry Type"), max_length=255, choices=INDCHOICES, blank=True, null=True)
    # billing_address = models.ForeignKey(
    #     Address, related_name='account_billing_address', on_delete=models.CASCADE, blank=True, null=True)
    # shipping_address = models.ForeignKey(
    #     Address, related_name='account_shipping_address', on_delete=models.CASCADE, blank=True, null=True)
    billing_address_line = models.CharField(_("Address"), max_length=255, blank=True, null=True)
    billing_street = models.CharField(_("Street"), max_length=55, blank=True, null=True)
    billing_city = models.CharField(_("City"), max_length=255, blank=True, null=True)
    billing_state = models.CharField(_("State"), max_length=255, blank=True, null=True)
    billing_postcode = models.CharField(_("Post/Zip-code"), max_length=64, blank=True, null=True)
    billing_country = models.CharField(max_length=3, choices=COUNTRIES, blank=True, null=True)
    website = models.URLField(_("Website"), blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='account_created_by', on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(_("Created on"), auto_now_add=True)
    is_active = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tags, blank=True)
    status = models.CharField(choices=ACCOUNT_STATUS_CHOICE, max_length=64, default='open')
    lead = models.ForeignKey('leads.Lead', related_name="account_leads", on_delete=models.SET_NULL, null=True)
    contact_name = models.CharField(pgettext_lazy("Name of Contact", "Contact Name"), max_length=120)
    contacts = models.ManyToManyField('contacts.Contact', related_name="account_contacts")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_on']

    def get_complete_address(self):
        address = ""
        if self.billing_address_line:
            address += self.billing_address_line
        if self.billing_street:
            if address:
                address += ", " + self.billing_street
            else:
                address += self.billing_street
        if self.billing_city:
            if address:
                address += ", " + self.billing_city
            else:
                address += self.billing_city
        if self.billing_state:
            if address:
                address += ", " + self.billing_state
            else:
                address += self.billing_state
        if self.billing_postcode:
            if address:
                address += ", " + self.billing_postcode
            else:
                address += self.billing_postcode
        if self.billing_country:
            if address:
                address += ", " + self.get_billing_country_display()
            else:
                address += self.get_billing_country_display()
        return address
