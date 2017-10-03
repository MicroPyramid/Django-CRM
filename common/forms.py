from django import forms
from common.models import Person
from oppurtunity.models import Opportunity
from cases.models import Case
from leads.models import Lead
from contacts.models import Contact
from accounts.models import Account


class OpportunityForm(forms.ModelForm):
    name = forms.CharField(max_length=255, required=True)
    stage = forms.CharField(max_length=255, required=True)

    class Meta:
        model = Opportunity
        fields = ['name',  'stage', 'amount', 'probability' , 'close_date', 'lead_source', 'description']


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ('name', 'account', 'email', 'phone', 'address', 'description')


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['first_name', 'last_name']


class CreateLeadform(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['title', 'name', 'email', 'description', 'account', 'website', 'status',
                  'source', 'opportunity_amount', 'description']


class TestTable(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # return the field you want to display
        return obj.name


class caseForm(forms.ModelForm):
    account = TestTable(queryset=Account.objects.all())

    # contacts = TestTableContacts(queryset=Contact.objects.all())

    class Meta:
        model = Case
        fields = "__all__"


# class RegistrationForm(forms.ModelForm):

#     class Meta:
#         model = CustomUser
#         fields = ('username', 'email', 'password')
#         widgets = {
#             'password': forms.PasswordInput(),
#         }
