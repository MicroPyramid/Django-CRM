from django import forms
from contacts.models import Contact
from common.models import Comment


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

    class Meta:
        model = Contact
        fields = (
            'assigned_to', 'teams', 'first_name', 'last_name', 'account', 'email', 'phone', 'address', 'description'
        )

    def clean_phone(self):
        client_phone = self.cleaned_data.get('phone', None)
        try:
            if int(client_phone) and not client_phone.isalpha():
                ph_length = str(client_phone)
                if len(ph_length) < 10 or len(ph_length) > 13:
                    raise forms.ValidationError('Phone number must be minimum 10 Digits and maximum of 13 Digits')
        except (ValueError):
            raise forms.ValidationError('Phone Number should contain only Numbers')
        return client_phone


class ContactCommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'contact', 'commented_by')
