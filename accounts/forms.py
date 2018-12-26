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
            value.widget.attrs['placeholder'] = value.label

    class Meta:
        model = Account
        fields = ('assigned_to', 'teams', 'name', 'phone', 'email', 'website', 'industry',
                  'billing_address', 'shipping_address', 'description')

    def clean_phone(self):
        client_phone = self.cleaned_data.get('phone', None)
        try:
            if int(client_phone) and not client_phone.isalpha():
                ph_length = str(client_phone)
                if len(ph_length) < 10 or len(ph_length) > 13:
                    raise forms.ValidationError('Phone number must be minimum 10 Digits and maximum of 13 Digits')
        except (ValueError, TypeError):
            raise forms.ValidationError('Phone Number should contain only Numbers')
        return client_phone


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
