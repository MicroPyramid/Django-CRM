from django.db import models
from djcrm.models import Address
from django.contrib.auth.models import User
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from accounts.models import LeadAccount


lead_status = (
    ('assigned', 'Assigned'),
    ('in process', 'In Process'),
    ('converted', 'Converted'),
    ('recycled', 'Recycled'),
    ('dead', 'Dead'),)


lead_source = (
    ('call', 'Call'),
    ('email', 'Email'),
    ('existing customer', 'Existing Customer'),
    ('partner', 'Partner'),
    ('public relations', 'Public Relations'),
    ('compaign', 'Campaign'),
    ('other', 'Other'),)


TEAMS = (
    ('SALES', 'SALES'),
    ('SUPPORT', 'SUPPORT'),
    ('TOP MANAGEMENT', 'TOP MANAGEMENT'),
)


class Lead(models.Model):
    title = models.CharField(
        pgettext_lazy(u"Treatment Pronouns for the customer", u"Title"),
        max_length=64, blank=True)
    name = models.CharField(("name"), max_length=255, blank=True)
    email = models.EmailField()
    created_date = models.DateTimeField(auto_now_add=True)
    assigned_user = models.ForeignKey(User, related_name='Leaduser', null=True)
    account = models.ForeignKey(LeadAccount, related_name='Leads', null=True)
    address = models.ForeignKey(Address, related_name='leadaddress', null=True)
    website = models.CharField(_("Website"), max_length=255, blank=True)
    status = models.CharField(_("Status of Lead"), max_length=255,
                              blank=True, choices=lead_status)
    source = models.CharField(_("Source of Lead"), max_length=255,
                              blank=True, choices=lead_source)
    opportunity_amount = models.DecimalField(
        _("Opportunity Amount"), decimal_places=2, max_digits=12,
        blank=True, null=True)
    # campaign = models.ForeignKey(Campaign, related_name='leads',null=True)
    description = models.TextField()
    phone = models.IntegerField(null=True)
    teams = models.CharField(max_length=255, choices=TEAMS, null=True)

    def __unicode__(self):
        return str(self.title)


class Comments(models.Model):
    leadid = models.ForeignKey(Lead, blank=True, null=True, default='')
    comment = models.CharField(max_length=255)
    comment_time = models.DateTimeField(auto_now_add=True)
    comment_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaduser', default='', blank=True, null=True)
