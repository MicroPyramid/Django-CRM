from django import forms
from contacts.models import Contact
from common.models import Comment, Attachments


class ContactForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        assigned_users = kwargs.pop('assigned_to', [])
        contact_account = kwargs.pop('account', [])
        super(ContactForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        self.fields['description'].widget.attrs.update({
            'rows': '6'})
        self.fields['assigned_to'].queryset = assigned_users
        self.fields['account'].queryset = contact_account
        self.fields['assigned_to'].required = False
        self.fields['teams'].required = False
        for key, value in self.fields.items():
            value.widget.attrs['placeholder'] = value.label

    class Meta:
        model = Contact
        fields = (
            'assigned_to', 'teams', 'first_name', 'last_name', 'account', 'email', 'phone', 'address', 'description'
        )


class ContactCommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'contact', 'commented_by')


class ContactAttachmentForm(forms.ModelForm):
    attachment = forms.FileField(max_length=1001, required=True)

    class Meta:
        model = Attachments
        fields = ('attachment', 'contact')
