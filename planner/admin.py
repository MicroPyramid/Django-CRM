from django.contrib import admin

from planner.models import Event
from planner.models import Reminder

# Register your models here.

admin.site.register(Event)
admin.site.register(Reminder)
