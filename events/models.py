import arrow

from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from common.models import User
from contacts.models import Contact
from teams.models import Teams
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
    teams = models.ManyToManyField(Teams, related_name='event_teams')

    # tags = models.ManyToManyField(Tag)

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_on).humanize()

    @property
    def get_team_users(self):
        team_user_ids = list(self.teams.values_list('users__id', flat=True))
        return User.objects.filter(id__in=team_user_ids)

    @property
    def get_team_and_assigned_users(self):
        team_user_ids = list(self.teams.values_list('users__id', flat=True))
        assigned_user_ids = list(self.assigned_to.values_list('id', flat=True))
        user_ids = team_user_ids + assigned_user_ids
        return User.objects.filter(id__in=user_ids)

    @property
    def get_assigned_users_not_in_teams(self):
        team_user_ids = list(self.teams.values_list('users__id', flat=True))
        assigned_user_ids = list(self.assigned_to.values_list('id', flat=True))
        user_ids = set(assigned_user_ids) - set(team_user_ids)
        return User.objects.filter(id__in=list(user_ids))