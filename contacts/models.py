import arrow
from django.db import models
from django.utils.translation import ugettext_lazy as _

from common.models import Address, User
from phonenumber_field.modelfields import PhoneNumberField
from teams.models import Teams


class Contact(models.Model):
    first_name = models.CharField(_("First name"), max_length=255)
    last_name = models.CharField(_("Last name"), max_length=255)
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(null=True, unique=True)
    address = models.ForeignKey(
        Address, related_name='adress_contacts',
        on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.ManyToManyField(
        User, related_name='contact_assigned_users')
    created_by = models.ForeignKey(
        User, related_name='contact_created_by',
        on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(_("Created on"), auto_now_add=True)
    is_active = models.BooleanField(default=False)
    teams = models.ManyToManyField(Teams, related_name='contact_teams')

    def __str__(self):
        return self.first_name

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_on).humanize()

    class Meta:
        ordering = ['-created_on']
