from django.db import models
from django.utils.translation import pgettext_lazy
from django.contrib.auth.models import User
from ..djcrm.models import Address
from ..accounts.models import LeadAccount


TEAMS = (
    ('SALES', 'SALES'),
    ('SUPPORT', 'SUPPORT'),
    ('TOP MANAGEMENT', 'TOP MANAGEMENT'),
)


class Contact(models.Model):
    teams = models.CharField(
        pgettext_lazy(u"Team in which the contact is in.", u"Team"),
        max_length=64, blank=True, choices=TEAMS)
    users = models.ForeignKey(User, related_name='created_contacts', blank=True, null=True)
    created_user = models.CharField(max_length=255, blank=True, null=True, default='')
    name = models.CharField(
        pgettext_lazy(u"Full name of the contact", u"Name"),
        max_length=64)
    email = models.EmailField()
    account = models.ForeignKey(LeadAccount, related_name='LeadAccount')
    phone = models.IntegerField()
    address = models.ForeignKey(Address, related_name='adress', blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Comments(models.Model):
    contactid = models.ForeignKey(Contact, blank=True, null=True, related_name="comment_create", on_delete=models.CASCADE, default='')
    comment = models.CharField(max_length=255)
    comment_time = models.DateTimeField(auto_now_add=True)
    comment_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="contact_comment",
        blank=True, null=True)
