from django import forms
from leads.models import Lead, Comments
from djcrm.models import Address


class CreateLeadform(forms.ModelForm):

    class Meta:
        model = Lead
        fields = ['title', 'name', 'email', 'description',
                  'account', 'website', 'status', 'phone', 'teams', 'assigned_user',
                  'source', 'opportunity_amount', 'description']

    def clean_phone(self):
        a = len(self.data.get("phone"))
        if (a == 10):
            return self.data.get("phone")
        else:
            raise forms.ValidationError("enter  valid phonenumber")


class AddressLeadForm(forms.ModelForm):

    class Meta:
        model = Address
        fields = ['street', 'city', 'state', 'postcode', 'country']


class CommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comments
        fields = ['comment', 'comment_user', 'leadid']
