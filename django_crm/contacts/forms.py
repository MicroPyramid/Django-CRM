from django import forms
from .models import Contact, Comments
from ..djcrm.models import Address


class AddressForm(forms.ModelForm):

    class Meta:

        model = Address
        fields = ('street', 'city', 'state', 'postcode', 'country')


class ContactForm(forms.ModelForm):

    class Meta:

        model = Contact
        fields = ('name', 'account', 'email', 'teams', 'users', 'phone', 'description')

    def clean_phone(self):
        a = len(self.data.get("phone"))
        if (a == 10):
            return self.data.get("phone")
        else:
            raise forms.ValidationError("enter a valid phone number with 10 digits")


class CommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comments
        fields = ('comment', 'comment_user', 'contactid')
