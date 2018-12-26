from django import forms
from leads.models import Lead
from common.models import Address, Comment, Attachments


class LeadForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        assigned_users = kwargs.pop('assigned_to', [])
        super(LeadForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        if self.data.get('status') == 'converted':
            self.fields['account_name'].required = True
        self.fields['assigned_to'].queryset = assigned_users
        self.fields['assigned_to'].required = False
        self.fields['teams'].required = False
        self.fields['phone'].required = True
        for key, value in self.fields.items():
            value.widget.attrs['placeholder'] = value.label
        self.fields['first_name'].widget.attrs.update({
            'placeholder': 'First Name'})
        self.fields['last_name'].widget.attrs.update({
            'placeholder': 'Last Name'})
        self.fields['account_name'].widget.attrs.update({
            'placeholder': 'Account Name'})

    class Meta:
        model = Lead
        fields = ('assigned_to', 'teams', 'first_name', 'last_name', 'account_name', 'title',
                  'phone', 'email', 'status', 'source', 'website', 'address', 'description'
                  )


class LeadCommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'lead', 'commented_by')


class LeadAttachmentForm(forms.ModelForm):
    attachment = forms.FileField(max_length=1001, required=True)

    class Meta:
        model = Attachments
        fields = ('attachment', 'lead')
