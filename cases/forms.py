from django import forms
from cases.models import Case
from common.models import Comment


class CaseForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        assigned_users = kwargs.pop('assigned_to', [])
        case_accounts = kwargs.pop('account', [])
        case_contacts = kwargs.pop('contacts', [])
        super(CaseForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        self.fields['description'].widget.attrs.update({
            'rows': '6'})
        self.fields['assigned_to'].queryset = assigned_users
        self.fields['account'].queryset = case_accounts
        self.fields['contacts'].queryset = case_contacts
        self.fields['assigned_to'].required = False
        self.fields['teams'].required = False
        self.fields['contacts'].required = False

    class Meta:
        model = Case
        fields = ('assigned_to', 'teams', 'name', 'status',
                  'priority', 'case_type', 'account',
                  'contacts', 'closed_on', 'description')

    def clean_name(self):
        name = self.cleaned_data['name']
        case = Case.objects.filter(name__iexact=name).exclude(id=self.instance.id)
        if case:
            raise forms.ValidationError("Case Already Exists with this Name")
        return name


class CaseCommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'case', 'commented_by', )