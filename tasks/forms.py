from django import forms
from tasks.models import Task
from accounts.models import Account
from contacts.models import Contact
from common.models import User, Attachments, Comment
from django.db.models import Q


class TaskForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        # assigned_users = kwargs.pop('assigned_to', [])
        request_user = kwargs.pop('request_user', None)
        self.obj_instance = kwargs.get('instance', None)
        super(TaskForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}

        if request_user.role == 'USER':
            self.fields["account"].queryset = Account.objects.filter(
                created_by=request_user).filter(status="open")

            self.fields["contacts"].queryset = Contact.objects.filter(
                Q(assigned_to__in=[request_user]) | Q(created_by=request_user))

        if request_user.role == 'ADMIN' or request_user.is_superuser:
            self.fields["account"].queryset = Account.objects.filter(status="open")

            self.fields["contacts"].queryset = Contact.objects.filter()

        self.fields['assigned_to'].required = False
        # if assigned_users:
        #     self.fields['assigned_to'].queryset = assigned_users
        # else:
        #     self.fields.get('assigned_to').queryset = User.objects.none()
        self.fields['title'].required = True
        self.fields['status'].required = True
        self.fields['priority'].required = True
        self.fields['account'].required = False
        self.fields['contacts'].required = False
        self.fields['due_date'].required = False

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not self.obj_instance:
            if Task.objects.filter(title=title).exists():
                raise forms.ValidationError(
                    'Task with this Title already exists')
            return title
        if Task.objects.filter(title=title).exclude(id=self.obj_instance.id).exists():
            raise forms.ValidationError(
                'Task with this Title already exists')
            return title
        return title

    class Meta:
        model = Task
        fields = (
            'title', 'status', 'priority', 'assigned_to', 'account', 'contacts',
            'due_date'
        )


class TaskCommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'task', 'commented_by')


class TaskAttachmentForm(forms.ModelForm):
    attachment = forms.FileField(max_length=1001, required=True)

    class Meta:
        model = Attachments
        fields = ('attachment', 'task')
