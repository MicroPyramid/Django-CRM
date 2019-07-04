from django.db import models
from common.models import User
from django.utils.translation import ugettext_lazy as _


class Teams(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    users = models.ManyToManyField(User, related_name='user_teams')
    created_on = models.DateTimeField(_("Created on"), auto_now_add=True)
    created_by = models.ForeignKey(
        User, related_name='teams_created', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)
