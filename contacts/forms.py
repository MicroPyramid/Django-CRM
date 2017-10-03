from django import forms
from contacts.models import Contact
from common.models import Comment
from common.models import Address


class AddressForm(forms.ModelForm):

    class Meta:

        model = Address
        fields = ('street', 'city', 'state', 'postcode', 'country')


class ContactForm(forms.ModelForm):

    class Meta:

        model = Contact
        fields = ('first_name', 'last_name', 'account', 'email', 'teams', 'assigned_to', 'phone', 'description')

    def clean_phone(self):
        a = len(self.data.get("phone"))
        if (a >= 10 and a <= 12):
            return self.data.get("phone")
        else:
            raise forms.ValidationError("Phone number must be Minimum of 10 Digits and Maximum of 12 Digits")


class CommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'commented_by', 'contact')
