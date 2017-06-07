from django.db import models
from ..djcrm.models import Address
from django.contrib.auth.models import User
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

# Create your models here.

INDCHOICES = (
    (u'ADVERTISING', u'ADVERTISING'),
    (u'AGRICULTURE', u'AGRICULTURE'),
    (u'APPAREL & ACCESSORIES', u'APPAREL & ACCESSORIES'),
    (u'AUTOMOTIVE', u'AUTOMOTIVE'),
    (u'BANKING', u'BANKING'),
    (u'BIOTECHNOLOGY', u'BIOTECHNOLOGY'),
    (u'BUILDING MATERIALS & EQUIPMENT', u'BUILDING MATERIALS & EQUIPMENT'),
    (u'CHEMICAL', u'CHEMICAL'),
    (u'COMPUTER', u'COMPUTER'),
    (u'EDUCATION', u'EDUCATION'),
    (u'ELECTRONICS', u'ELECTRONICS'),
    (u'ENERGY', u'ENERGY'),
    (u'ENTERTAINMENT & LEISURE', u'ENTERTAINMENT & LEISURE'),
    (u'FINANCE', u'FINANCE'),
    (u'FOOD & BEVERAGE', u'FOOD & BEVERAGE'),
    (u'GROCERY', u'GROCERY'),
    (u'HEALTHCARE', u'HEALTHCARE'),
    (u'INSURANCE', u'INSURANCE'),
    (u'LEGAL', u'LEGAL'),
    (u'MANUFACTURING', u'MANUFACTURING'),
    (u'PUBLISHING', u'PUBLISHING'),
    (u'REAL ESTATE', u'REAL ESTATE'),
    (u'SERVICE', u'SERVICE'),
    (u'SOFTWARE', u'SOFTWARE'),
    (u'SPORTS', u'SPORTS'),
    (u'TECHNOLOGY', u'TECHNOLOGY'),
    (u'TELECOMMUNICATIONS', u'TELECOMMUNICATIONS'),
    (u'TELEVISION', u'TELEVISION'),
    (u'TRANSPORTATION', u'TRANSPORTATION'),
    (u'VENTURE CAPITAL', u'VENTURE CAPITAL'),
)

TYPECHOICES = (
    (u'CUSTOMER', u'CUSTOMER'),
    (u'INVESTOR', u'INVESTOR'),
    (u'PARTNER', u'PARTNER'),
    (u'RESELLER', u'RESELLER'),
)

TEAMS = (
    (u'SALES DEPARTMENT', u'SALES DEPARTMENT'),
    (u'SUPPORT', u'SUPPORT'),
    (u'TOP MANAGEMENT', u'TOP MANAGEMENT'),
)


class LeadAccount(models.Model):
    name = models.CharField(
        pgettext_lazy(u"Name of Account", u"Name"),
        max_length=64)
    email = models.EmailField()
    phone = models.IntegerField()
    billing_address = models.ForeignKey(Address, related_name='lead', blank=True, null=True)
    shipping_address = models.ForeignKey(Address, related_name='lead1', blank=True, null=True)
    website = models.URLField(_("Website"), blank=True, null=True)
    account_type = models.CharField(_("Account Type"), max_length=255, choices=TYPECHOICES, blank=True)
    sis_code = models.CharField(_("Sis code of the company"), max_length=255, blank=True, null=True)
    industry = models.CharField(_("Industry Type"), max_length=255, choices=INDCHOICES, blank=True)
    description = models.TextField(blank=True)
    date = models.DateField(_("Date"), auto_now_add=True)
    teams = models.CharField(_("Teams"), max_length=255, choices=TEAMS, blank=True)
    users = models.ForeignKey(User, blank=True, null=True)
    assigned_user = models.CharField(max_length=255, blank=True, null=True, default='')

    def __str__(self):
        return self.name

    def get_assigned_user(self):
        return User.objects.get(id=self.assigned_user)


class Comment(models.Model):
    accountid = models.ForeignKey(LeadAccount, blank=True, null=True, related_name="accounts", on_delete=models.CASCADE , default='')
    comment = models.CharField(max_length=255)
    comment_date = models.DateTimeField(auto_now_add=True)
    comment_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='users', default='', blank=True, null=True)
