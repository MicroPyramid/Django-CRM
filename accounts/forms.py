from django import forms
from .models import Account
from common.models import Comment, Attachments


class AccountForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        assigned_users = kwargs.pop('assigned_to', [])
        super(AccountForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        self.fields['description'].widget.attrs.update({'rows': '8'})
        self.fields['assigned_to'].queryset = assigned_users
        self.fields['assigned_to'].required = False
        self.fields['teams'].required = False
        for key, value in self.fields.items():
            if key == 'phone':
                value.widget.attrs['placeholder'] = "+91-123-456-7890"
            else:
                value.widget.attrs['placeholder'] = value.label

    class Meta:
        model = Account
        fields = ('assigned_to', 'teams', 'name', 'phone', 'email', 'website', 'industry',
                  'billing_address', 'shipping_address', 'description')


class AccountCommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'account', 'commented_by')


class AccountAttachmentForm(forms.ModelForm):
    attachment = forms.FileField(max_length=1001, required=True)

    class Meta:
        model = Attachments
        fields = ('attachment', 'account')
