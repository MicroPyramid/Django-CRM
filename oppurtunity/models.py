from django.utils.translation import ugettext_lazy as _
from django.utils.translation import pgettext_lazy
from django.db import models
from django.contrib.auth.models import User
from accounts.models import LeadAccount
from contacts.models import Contact


# Create your models here.

STAGES = (
    (u'QUALIFICATION', u'QUALIFICATION'),
    (u'NEEDS ANALYSIS', u'NEEDS ANALYSIS'),
    (u'VALUE PROPOSITION', u'VALUE PROPOSITION'),
    (u'ID.DECISION MAKERS', u'ID.DECISION MAKERS'),
    (U'PERCEPTION ANALYSIS', U'PERCEPTION ANALYSIS'),
    (U'PROPOSAL/PRICE QUOTE', U'PROPOSAL/PRICE QUOTE'),
    (U'NEGOTIATION/REVIEW', U'NEGOTIATION/REVIEW'),
    (U'CLOSED WON', U'CLOSED WON'),
    (U'CLOSED LOST', U'CLOSED LOST'),
)

SOURCES = (
    (u'NONE', u'NONE'),
    (u'CALL', u'CALL'),
    (u'EMAIL', u' EMAIL'),
    (u'EXISTING CUSTOMER', u'EXISTING CUSTOMER'),
    (u'PARTNER', u'PARTNER'),
    (u'PUBLIC RELATIONS', u'PUBLIC RELATIONS'),
    (u'CAMPAIGN', u'CAMPAIGN'),
    (u'WEBSITE', u'WEBSITE'),
    (u'OTHER', u'OTHER'),
)

TEAMS = (
    ('SALES DEPARTMENT', 'SALES DEPARTMENT'),
    ('SUPPORT', 'SUPPORT'),
    ('TOP MANAGEMENT', 'TOP MANAGEMENT'),
)


class Opportunity(models.Model):
    name = models.CharField(
        pgettext_lazy(u"Name of the Opportunity", u"Name"),
        max_length=64)
    account = models.ForeignKey(
        LeadAccount, related_name='opportunities', blank=True, null=True)
    stage = models.CharField(
        pgettext_lazy(u"Stage at which the Opportunity is in.", u"Stage"),
        max_length=64, choices=STAGES)
    amount = models.IntegerField()
    probability = models.IntegerField()
    close_date = models.DateField()
    contacts = models.ManyToManyField(Contact, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    lead_source = models.CharField(_(
        "Source of Lead"), max_length=255, choices=SOURCES, blank=True)
    description = models.TextField(blank=True)
    users = models.ForeignKey(
        User, max_length=255, blank=True, null=True)
    assigned_user = models.CharField(max_length=255, blank=True, null=True, default='')
    teams = models.CharField(
        max_length=255, choices=TEAMS, blank=True, null=True)

    def __str__(self):
        return self.name

    def get_created_user(self):
        return User.objects.get(id=self.created_user)


class Comments(models.Model):
    oppid = models.ForeignKey(Opportunity, blank=True, null=True, default='')
    comment = models.CharField(max_length=255)
    comment_time = models.DateTimeField(auto_now_add=True)
    comment_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user', default='', blank=True, null=True)
