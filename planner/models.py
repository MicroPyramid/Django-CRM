from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from contacts.models import Contact
from leads.models import Lead


# Create your models here.


class Reminder(models.Model):
    reminder_type = models.CharField(max_length=5, blank=True,
                                     null=True)
    reminder_time = models.IntegerField(pgettext_lazy(u"time of the reminder to event in Seconds", u"Reminder"),
                                        blank=True, null=True)

    def __str__(self):
        return self.reminder_type


class Event(models.Model):
    parentChoices = ((10, 'Account'), (13, 'Lead'), (14, 'Opportunity'), (11, 'Case'))
    statusChoices = (
        ('Planned', 'Planned'), ('Held', 'Held'), ('Not Held', 'Not Held'), ('Not Started', 'Not Started'),
        ('Started', 'Started'), ('Completed', 'Completed'), ('Canceled', 'Canceled'), ('Deferred', 'Deferred'))
    teamsChoices = (
        ('Sales Department', 'Sales Department'), ('Support', 'Support'), ('Top Management', 'Top Management'))
    limit = models.Q(app_label='account', model='LeadAccount', id=10) | \
            models.Q(app_label='leads', model='Lead', id=13) | \
            models.Q(app_label='oppurtunity', model='Opportunity', id=14) | \
            models.Q(app_label='cases', model='Case', id=11)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(
        pgettext_lazy(u"Name of the Event", u"Event"),
        max_length=64)
    event_type = models.CharField(_("Type of the event"), max_length=7)  # call meeting task

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True,
                                     limit_choices_to=limit, choices=parentChoices)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    parent = GenericForeignKey('content_type', 'object_id')

    status = models.CharField(
        pgettext_lazy(u"status of the Event", u"Status"), choices=statusChoices,
        max_length=64, blank=True)
    direction = models.CharField(max_length=20, blank=True)  # only for calls
    start_date = models.DateTimeField(default=None)
    close_date = models.DateTimeField(default=None, null=True)
    description = models.TextField(max_length=200, null=True, blank=True)
    duration = models.IntegerField(pgettext_lazy(u"Duration of the Event in Seconds", u"Durations"), default=None,
                                   null=True)  # not for tasks
    reminders = models.ManyToManyField(Reminder, blank=True)
    priority = models.CharField(max_length=10, blank=True)  # only for task

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_user')
    updated_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='updated_user')

    assigned_users = models.ForeignKey(User,
                                       related_name='assigned_users',
                                       on_delete=models.CASCADE, null=True, blank=True)

    attendees_user = models.ManyToManyField(User, blank=True,
                                            related_name='attendees_user')
    attendees_contacts = models.ManyToManyField(Contact, blank=True,
                                                related_name='attendees_contact')
    attendees_leads = models.ManyToManyField(Lead, blank=True,
                                             related_name='attendees_lead')
    teams = models.CharField(choices=teamsChoices, null=True, blank=True, max_length=20)

    def __str__(self):
        return self.name
