import arrow
from django.db import models
from common.models import Profile, Org
from accounts.models import Account
from contacts.models import Contact
from django.utils.translation import ugettext_lazy as _
from teams.models import Teams


class Task(models.Model):

    STATUS_CHOICES = (
        ("New", "New"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
    )

    PRIORITY_CHOICES = (("Low", "Low"), ("Medium", "Medium"), ("High", "High"))

    title = models.CharField(_("title"), max_length=200)
    status = models.CharField(_("status"), max_length=50, choices=STATUS_CHOICES)
    priority = models.CharField(_("priority"), max_length=50, choices=PRIORITY_CHOICES)
    due_date = models.DateField(blank=True, null=True)
    created_on = models.DateTimeField(_("Created on"), auto_now_add=True)
    account = models.ForeignKey(
        Account,
        related_name="accounts_tasks",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    contacts = models.ManyToManyField(Contact, related_name="contacts_tasks")

    assigned_to = models.ManyToManyField(Profile, related_name="users_tasks")

    created_by = models.ForeignKey(
        Profile,
        related_name="task_created",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    teams = models.ManyToManyField(Teams, related_name="tasks_teams")
    org = models.ForeignKey(
        Org, on_delete=models.SET_NULL, null=True, blank=True, related_name="task_org"
    )

    class Meta:
        ordering = ["-due_date"]

    def __str__(self):
        return self.title

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_on).humanize()

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
