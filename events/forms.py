from django import forms
from contacts.models import Contact
from common.models import User, Attachments, Comment
from django.db.models import Q
from events.models import Event
from teams.models import Teams


class EventForm(forms.ModelForm):

    WEEKDAYS = (('Monday', 'Monday'),
                ('Tuesday', 'Tuesday'),
                ('Wednesday', 'Wednesday'),
                ('Thursday', 'Thursday'),
                ('Friday', 'Friday'),
                ('Saturday', 'Saturday'),
                ('Sunday', 'Sunday'))

    recurring_days = forms.MultipleChoiceField(
        required=False, choices=WEEKDAYS)

    teams_queryset = []
    teams = forms.MultipleChoiceField(choices=teams_queryset)

    def __init__(self, *args, **kwargs):
        request_user = kwargs.pop('request_user', None)
        self.obj_instance = kwargs.get('instance', None)
        super(EventForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}

        if request_user.role == 'ADMIN' or request_user.is_superuser:
            self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
            self.fields["contacts"].queryset = Contact.objects.filter()
            self.fields['assigned_to'].required = True
            self.fields["teams"].choices = [(team.get('id'), team.get('name')) for team in Teams.objects.all().values('id', 'name')]
        # elif request_user.google.all():
        #     self.fields['assigned_to'].queryset = User.objects.none()
        #     self.fields["contacts"].queryset = Contact.objects.filter(
        #         Q(assigned_to__in=[request_user]) | Q(created_by=request_user))
        #     self.fields['assigned_to'].required = False
        elif request_user.role == 'USER':
            self.fields['assigned_to'].queryset = User.objects.filter(
                role='ADMIN')
            self.fields["contacts"].queryset = Contact.objects.filter(
                Q(assigned_to__in=[request_user]) | Q(created_by=request_user))
            self.fields['assigned_to'].required = True
        else:
            pass
        if self.obj_instance:
            # self.fields['name'].widget.attrs['readonly'] = True
            self.fields['start_date'].widget.attrs['readonly'] = True
            self.fields['end_date'].widget.attrs['readonly'] = True

        self.fields["teams"].required = False
        self.fields['name'].required = True
        self.fields['event_type'].required = True
        self.fields['contacts'].required = True
        self.fields['start_date'].required = True
        self.fields['start_time'].required = True
        self.fields['end_date'].required = True
        self.fields['end_time'].required = True
        self.fields['description'].required = False

    def clean_recurring_days(self):
        recurring_days = self.cleaned_data.get('recurring_days')
        if not self.obj_instance:
            if self.cleaned_data.get('event_type') == 'Recurring':
                if len(recurring_days) < 1:
                    raise forms.ValidationError('Choose atleast one recurring day')

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not self.obj_instance:
            if Event.objects.filter(name=name).exclude(id=self.instance.id).exists():
                raise forms.ValidationError(
                    'Event with this name already exists.')

        return name

    def clean_event_type(self):
        """ This Validation Is For Keeping The Field Readonly While Editing or Updating"""
        event_type = self.cleaned_data.get('event_type')
        if self.obj_instance:
            return self.obj_instance.event_type
        else:
            return event_type

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date:
            if self.obj_instance:
                return self.obj_instance.start_date
            else:
                return start_date
        else:
            raise forms.ValidationError('Enter a valid Start date.')

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        event_type = self.cleaned_data.get('event_type')
        if event_type == 'Recurring':
            if self.clean_start_date() == end_date:
                raise forms.ValidationError(
                    'Start Date and End Date cannot be equal for recurring events')
        if self.clean_start_date() > end_date:
            raise forms.ValidationError(
                'End Date cannot be less than start date')
        return end_date

    def clean_end_time(self):
        end_time = self.cleaned_data.get('end_time')
        if not self.cleaned_data.get('start_time'):
            raise forms.ValidationError('Enter a valid start time.')
        if self.cleaned_data.get('start_time') > end_time:
            raise forms.ValidationError(
                'End Time cannot be less than Start Time')
        return end_time

    class Meta:
        model = Event
        fields = (
            'name', 'event_type', 'contacts', 'assigned_to', 'start_date', 'start_time',
            'end_date', 'end_time', 'description',
        )


class EventCommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=255, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'event', 'commented_by')


class EventAttachmentForm(forms.ModelForm):
    attachment = forms.FileField(max_length=1001, required=True)

    class Meta:
        model = Attachments
        fields = ('attachment', 'event')
