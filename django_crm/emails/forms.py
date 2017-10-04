from django import forms
from .models import Email


class EmailForm(forms.ModelForm):

    from_email = forms.EmailField(max_length=200, required=True)
    to_email = forms.EmailField(max_length=200, required=True)
    subject = forms.CharField(max_length=200, required=True)
    message = forms.CharField(max_length=200, required=True)

    class Meta:
        model = Email
        fields = ('from_email', 'to_email', 'subject', 'message')
