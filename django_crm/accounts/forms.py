from django import forms
from .models import LeadAccount, Comment
from ..djcrm.models import Address


class AccountForm(forms.ModelForm):

    class Meta:
        model = LeadAccount
        fields = ['name', 'email', 'phone', 'website', 'account_type',
                  'sis_code', 'industry', 'description', 'teams', 'users']
    phone = forms.RegexField(regex=r'(^[0-9]{10,12}$)', error_messages={'invalid': ("Phone number must be Minimum of 4 Digits and Maximum of 13 Digits.")})

    # def clean_website(self):
    #     website = self.cleaned_data['website']
    #     val = validators.url(website)
    #     if val:
    #         raise forms.ValidationError("Enter Valid URL")
    #     else:
    #         return website


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
