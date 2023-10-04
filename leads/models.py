import arrow
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from phonenumber_field.modelfields import PhoneNumberField

from accounts.models import Tags
from common.models import Org, Profile
from common.base import BaseModel
from common.utils import (
    COUNTRIES,
    INDCHOICES,
    LEAD_SOURCE,
    LEAD_STATUS,
    return_complete_address,
)
from contacts.models import Contact
from teams.models import Teams


class Company(BaseModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    org = models.ForeignKey(Org, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        db_table = "company"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name}"

class Lead(BaseModel):
    title = models.CharField(
        pgettext_lazy("Treatment Pronouns for the customer", "Title"), max_length=64
    )
    first_name = models.CharField(_("First name"), null=True, max_length=255)
    last_name = models.CharField(_("Last name"), null=True, max_length=255)
    email = models.EmailField(null=True, blank=True)
    phone = PhoneNumberField(null=True, blank=True)
    status = models.CharField(
        _("Status of Lead"), max_length=255, blank=True, null=True, choices=LEAD_STATUS
    )
    source = models.CharField(
        _("Source of Lead"), max_length=255, blank=True, null=True, choices=LEAD_SOURCE
    )
    address_line = models.CharField(_("Address"), max_length=255, blank=True, null=True)
    street = models.CharField(_("Street"), max_length=55, blank=True, null=True)
    city = models.CharField(_("City"), max_length=255, blank=True, null=True)
    state = models.CharField(_("State"), max_length=255, blank=True, null=True)
    postcode = models.CharField(
        _("Post/Zip-code"), max_length=64, blank=True, null=True
    )
    country = models.CharField(max_length=3, choices=COUNTRIES, blank=True, null=True)
    website = models.CharField(_("Website"), max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.ManyToManyField(Profile, related_name="lead_assigned_users")
    account_name = models.CharField(max_length=255, null=True, blank=True)
    opportunity_amount = models.DecimalField(
        _("Opportunity Amount"), decimal_places=2, max_digits=12, blank=True, null=True
    )
    is_active = models.BooleanField(default=False)
    enquiry_type = models.CharField(max_length=255, blank=True, null=True)
    tags = models.ManyToManyField(Tags, blank=True)
    contacts = models.ManyToManyField(Contact, related_name="lead_contacts")
    created_from_site = models.BooleanField(default=False)
    teams = models.ManyToManyField(Teams, related_name="lead_teams")
    org = models.ForeignKey(
        Org, on_delete=models.SET_NULL, null=True, blank=True, related_name="lead_org"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_company",
    )
    skype_ID = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(
        _("Industry Type"), max_length=255, choices=INDCHOICES, blank=True, null=True
    )
    organization = models.CharField(_("Organization"), max_length=255, null=True)
    probability = models.IntegerField(default=0, blank=True, null=True)
    close_date = models.DateField(default=None, null=True)

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        db_table = "lead"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.title}"

    def get_complete_address(self):
        return return_complete_address(self)

    @property
    def phone_raw_input(self):
        if str(self.phone) == "+NoneNone":
            return ""
        return self.phone

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_at).humanize()

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

    # def save(self, *args, **kwargs):
    #     super(Lead, self).save(*args, **kwargs)
    #     queryset = Lead.objects.all().exclude(status='converted').select_related('created_by'
    #         ).prefetch_related('tags', 'assigned_to',)
    #     open_leads = queryset.exclude(status='closed')
    #     close_leads = queryset.filter(status='closed')
    #     cache.set('admin_leads_open_queryset', open_leads, 60*60)
    #     cache.set('admin_leads_close_queryset', close_leads, 60*60)
