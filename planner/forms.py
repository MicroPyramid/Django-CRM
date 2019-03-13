from django import forms
from planner.models import Reminder


# class EventForm(forms.ModelForm):
#     class Meta:
#         model = Event
#         fields = ['name', 'status', 'start_date', 'description', 'assigned_to', 'attendees_user',
#                   'attendees_contacts', 'attendees_leads']

#     start_date = forms.DateTimeField(input_formats=['%m/%d/%Y %H:%M:%S'], error_messages={
#         'invalid': ("Invalid Startdate")}, required=True)
#     parent_id = forms.IntegerField(required=False)
#     parent_typeChoices = (
#         ('Account', 'Account'), ('Lead', 'Lead'), ('Opportunity', 'Opportunity'),
#         ('Case', 'Case'))
#     parent_type = forms.ChoiceField(choices=parent_typeChoices, error_messages={
#         'invalid': ("Invalid parent_type selected.")}, required=False)


# class TaskEventForm(EventForm):
#     class Meta(EventForm.Meta):
#         model = Event
#         fields = ['priority', 'close_date', 'event_type'] + EventForm.Meta.fields

#     parent_typeChoices = (
#         ('Account', 'Account'), ('Contact', 'Contact'), ('Lead', 'Lead'), ('Opportunity', 'Opportunity'),
#         ('Case', 'Case'))
#     parent_type = forms.ChoiceField(choices=parent_typeChoices, error_messages={
#         'invalid': ("Invalid parent_type selected.")}, required=False)
#     priority = forms.ChoiceField(choices=(('Low', 'Low'), ('Normal', 'Normal'), ('High', 'High'), ('Urgent', 'Urgent')),
#                                  error_messages={
#                                      'invalid': ("Invalid Priority selected.")}, required=True)  # only tasks
#     close_date = forms.DateTimeField(input_formats=['%m/%d/%Y %H:%M:%S'], required=True)


# class CallEventForm(EventForm):
#     class Meta(EventForm.Meta):
#         model = Event
#         fields = ['direction', 'duration', 'event_type'] + EventForm.Meta.fields

#     direction = forms.ChoiceField(choices=(('Outbound', 'Outbound'),
#                                            ('Inbound', 'Inbound')), error_messages={
#         'invalid': ("Invalid Direction selected.")}, required=True)  # only calls
#     duration = forms.ChoiceField(choices=(("300", "5m"),
#                                           ("600", "10m"),
#                                           ("900", "15m"),
#                                           ("1800", "30m"),
#                                           ("2700", "45m"),
#                                           ("3600", "1h"),
#                                           ("7600", "2h")), error_messages={
#         'invalid': ("Invalid Duration selected.")}, required=True)  # not for tasks


class ReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = '__all__'

    reminder_type = forms.ChoiceField(choices=(
        ('Email', 'Email'), ('Popup', 'Popup')),
        widget=forms.Select(attrs={
            'class': 'form-control input-sm'}))
    reminder_time = forms.ChoiceField(choices=(("0", "on time"),
                                               ("60", "1m before"),
                                               ("120", "2m before"),
                                               ("300", "5m before"),
                                               ("600", "10m before"),
                                               ("900", "15m before"),
                                               ("1800", "30m before"),
                                               ("3600", "1h before"),
                                               ("7200", "2h before"),
                                               ("10800", "3h before"),
                                               ("18000", "5h before"),
                                               ("86400", "1d before")
                                               ),
                                      widget=forms.Select(attrs={
                                          'class': 'form-control input-sm'}))


# class MeetingEventForm(EventForm):
#     class Meta(EventForm.Meta):
#         model = Event
#         fields = ['duration', 'close_date', 'event_type', ] + EventForm.Meta.fields

#     duration = forms.ChoiceField(choices=(
#         ("900", "15m"),
#         ("1800", "30m"),
#         ("3600", "1h"),
#         ("7200", "2h"),
#         ("10800", "3h"),
#         ("86400", "1d")
#     ), error_messages={
#         'invalid': ("Invalid Duration selected.")}, required=True)  # not for tasks
#     close_date = forms.DateTimeField(input_formats=['%m/%d/%Y %H:%M:%S'], required=True)
