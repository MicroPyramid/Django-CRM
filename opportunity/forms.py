from django import forms
from opportunity.models import Opportunity
from common.models import Comment


class OpportunityForm(forms.ModelForm):
    probability = forms.IntegerField(max_value=100, required=False)

    def __init__(self, *args, **kwargs):
        assigned_users = kwargs.pop('assigned_to', [])
        opp_accounts = kwargs.pop('account', [])
        opp_contacts = kwargs.pop('contacts', [])
        super(OpportunityForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        self.fields['description'].widget.attrs.update({
            'rows': '8'})
        self.fields['assigned_to'].queryset = assigned_users
        self.fields['account'].queryset = opp_accounts
        self.fields['contacts'].queryset = opp_contacts
        self.fields['assigned_to'].required = False
        self.fields['teams'].required = False
        self.fields['contacts'].required = False
        for key, value in self.fields.items():
            value.widget.attrs['placeholder'] = value.label
        self.fields['probability'].widget.attrs.update({
            'placeholder': 'Probability'})

    class Meta:
        model = Opportunity
        fields = (
            'name', 'amount', 'account', 'contacts', 'assigned_to', 'currency',
            'probability', 'teams', 'closed_on', 'lead_source', 'description', 'stage',
        )


class OpportunityCommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'opportunity', 'commented_by')
