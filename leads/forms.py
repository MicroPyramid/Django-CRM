from django import forms
from leads.models import Lead
from common.models import Comment
from common.models import Address


class CreateLeadform(forms.ModelForm):

    class Meta:
        model = Lead
        fields = ['title', 'first_name', 'last_name', 'email', 'description',
                  'account', 'website', 'status', 'phone', 'teams', 'assigned_to',
                  'source', 'opportunity_amount', 'description']

    def clean_phone(self):
        a = len(self.data.get("phone"))
        if (a >= 10 and a <= 12):
            return self.data.get("phone")
        else:
            raise forms.ValidationError("Phone number must be Minimum of 10 Digits and Maximum of 12 Digits")


class AddressLeadForm(forms.ModelForm):

    class Meta:
        model = Address
        fields = ['street', 'city', 'state', 'postcode', 'country']


class CommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comment
        fields = ['comment', 'commented_by', 'lead']
