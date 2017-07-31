from django.contrib import admin

from .models import Event,Reminder
# Register your models here.
admin.site.register(Event)
admin.site.register(Reminder)