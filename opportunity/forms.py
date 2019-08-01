from django import forms
from opportunity.models import Opportunity
from common.models import Comment, Attachments
from teams.models import Teams


class OpportunityForm(forms.ModelForm):
    probability = forms.IntegerField(max_value=100, required=False)
    teams_queryset = []
    teams = forms.MultipleChoiceField(choices=teams_queryset)

    def __init__(self, *args, **kwargs):
        assigned_users = kwargs.pop('assigned_to', [])
        opp_accounts = kwargs.pop('account', [])
        opp_contacts = kwargs.pop('contacts', [])
        super(OpportunityForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        self.fields['description'].widget.attrs.update({
            'rows': '8'})
        if assigned_users:
            self.fields['assigned_to'].queryset = assigned_users
        self.fields['assigned_to'].required = False
        self.fields['account'].queryset = opp_accounts
        self.fields['contacts'].queryset = opp_contacts
        self.fields['contacts'].required = False
        for key, value in self.fields.items():
            value.widget.attrs['placeholder'] = value.label

        self.fields['closed_on'].widget.attrs.update({
            'placeholder': 'Due Date'})

        self.fields['probability'].widget.attrs.update({
            'placeholder': 'Probability'})
        self.fields["teams"].choices = [(team.get('id'), team.get('name')) for team in Teams.objects.all().values('id', 'name')]
        self.fields["teams"].required = False

    class Meta:
        model = Opportunity
        fields = (
            'name', 'amount', 'account', 'contacts', 'assigned_to', 'currency',
            'probability', 'closed_on', 'lead_source', 'description', 'stage',
        )


class OpportunityCommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=255, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'opportunity', 'commented_by')


class OpportunityAttachmentForm(forms.ModelForm):
    attachment = forms.FileField(max_length=1001, required=True)

    class Meta:
        model = Attachments
        fields = ('attachment', 'opportunity')
