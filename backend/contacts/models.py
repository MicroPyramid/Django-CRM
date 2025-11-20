import arrow
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from common.models import Org, Profile
from common.base import BaseModel
from common.utils import COUNTRIES
from teams.models import Teams


class Contact(BaseModel):
    """
    Contact model for CRM - Streamlined for modern sales workflow
    Based on Twenty CRM and Salesforce patterns
    """
    # Core Contact Information
    first_name = models.CharField(_("First name"), max_length=255)
    last_name = models.CharField(_("Last name"), max_length=255)
    primary_email = models.EmailField(_("Email"), blank=True, null=True)
    mobile_number = PhoneNumberField(_("Phone"), null=True, blank=True)

    # Professional Information
    organization = models.CharField(_("Company"), max_length=255, blank=True, null=True)
    title = models.CharField(_("Job Title"), max_length=255, blank=True, null=True)
    department = models.CharField(_("Department"), max_length=255, blank=True, null=True)

    # Communication Preferences
    do_not_call = models.BooleanField(_("Do Not Call"), default=False)
    linked_in_url = models.URLField(_("LinkedIn URL"), blank=True, null=True)

    # Address (flat fields like Lead model)
    address_line = models.CharField(_("Address"), max_length=255, blank=True, null=True)
    city = models.CharField(_("City"), max_length=255, blank=True, null=True)
    state = models.CharField(_("State"), max_length=255, blank=True, null=True)
    postcode = models.CharField(_("Postal Code"), max_length=64, blank=True, null=True)
    country = models.CharField(_("Country"), max_length=3, choices=COUNTRIES, blank=True, null=True)

    # Assignment
    assigned_to = models.ManyToManyField(Profile, related_name="contact_assigned_users")
    teams = models.ManyToManyField(Teams, related_name="contact_teams")

    # Notes
    description = models.TextField(_("Notes"), blank=True, null=True)

    # System Fields
    is_active = models.BooleanField(default=False)
    org = models.ForeignKey(Org, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        db_table = "contacts"
        ordering = ("-created_at",)

    def __str__(self):
        return self.first_name

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_at).humanize()
    
    @property
    def created_on(self):
        return self.created_at


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
