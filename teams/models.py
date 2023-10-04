import arrow
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import Org, Profile
from common.base import BaseModel



class Teams(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    users = models.ManyToManyField(Profile, related_name="user_teams")
    created_on = models.DateTimeField(_("Created on"), auto_now_add=True)
    org = models.ForeignKey(Org, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        db_table = "teams"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name}"
    
    @property
    def created_on_arrow(self):
        return arrow.get(self.created_on).humanize()

    def get_users(self):
        return ",".join(
            [str(_id) for _id in list(self.users.values_list("id", flat=True))]
        )
        # return ','.join(list(self.users.values_list('id', flat=True)))
