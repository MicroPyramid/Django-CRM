from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from common.models import User
from contacts.models import Contact
# Create your models here.


class Event(models.Model):
    EVENT_TYPE = (
        ('Recurring', 'Recurring'),
        ('Non-Recurring', 'Non-Recurring'),
        # ("Call", "Call"),
        # ('Meeting', 'Meeting'),
        # ('Task', 'Task')
    )
    EVENT_STATUS = (
        ('Planned', 'Planned'),
        ('Held', 'Held'),
        ('Not Held', 'Not Held'),
        ('Not Started', 'Not Started'),
        ('Started', 'Started'),
        ('Completed', 'Completed'),
        ('Canceled', 'Canceled'),
        ('Deferred', 'Deferred')
    )
    name = models.CharField(_("Event"), max_length=64)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE)
    status = models.CharField(choices=EVENT_STATUS, max_length=64, blank=True, null=True)
    contacts = models.ManyToManyField(
        Contact, blank=True, related_name='event_contact')
    assigned_to = models.ManyToManyField(
        User, blank=True, related_name='event_assigned')
    start_date = models.DateField(default=None)
    start_time = models.TimeField(default=None)
    end_date = models.DateField(default=None)
    end_time = models.TimeField(default=None, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(_("Created on"), auto_now_add=True)
    created_by = models.ForeignKey(
        User, related_name='event_created_by_user', null=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    disabled = models.BooleanField(default=False)
    date_of_meeting = models.DateField(blank=True, null=True)
    # tags = models.ManyToManyField(Tag)
