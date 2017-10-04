from django import forms
from .models import Account
from common.models import Address, Comment


class AccountForm(forms.ModelForm):

    class Meta:
        model = Account
        fields = ['name', 'email', 'phone', 'website',
                  'industry', 'description', 'teams', 'assigned_to']
    phone = forms.RegexField(regex=r'(^[0-9]{10,12}$)', error_messages={'invalid': ("Phone number must be Minimum of 10 Digits and Maximum of 12 Digits.")})


class BillingAddressForm(forms.ModelForm):

    class Meta:
        model = Address
        exclude = []


class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = []

    def __init__(self, *args, **kwargs):
        super(ShippingAddressForm, self).__init__(*args, **kwargs)


class CommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comment
        fields = ['comment', ]
        exclude = ('comment_date', 'comment_user', 'accountid')


# class CountryBillingForm(forms.ModelForm):
#     class Meta:
#         model = Country
#         fields = ['printable_name', ]


# class CountryShippingForm(forms.ModelForm):
#     class Meta:
#         model = Country
#         fields = ['printable_name', ]
