from django import forms
from .models import Account
from common.models import Comment, Attachments, User
from leads.models import Lead
from contacts.models import Contact
from django.db.models import Q
from teams.models import Teams


class AccountForm(forms.ModelForm):
    teams_queryset = []
    teams = forms.MultipleChoiceField(choices=teams_queryset)

    def __init__(self, *args, **kwargs):
        account_view = kwargs.pop('account', False)
        request_user = kwargs.pop('request_user', None)
        super(AccountForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        self.fields['description'].widget.attrs.update({'rows': '8'})
        self.fields['status'].choices = [
            (each[0], each[1]) for each in Account.ACCOUNT_STATUS_CHOICE]
        self.fields['status'].required = False
        for key, value in self.fields.items():
            if key == 'phone':
                value.widget.attrs['placeholder'] = "+91-123-456-7890"
            else:
                value.widget.attrs['placeholder'] = value.label

        self.fields['billing_address_line'].widget.attrs.update({
            'placeholder': 'Address Line'})
        self.fields['billing_street'].widget.attrs.update({
            'placeholder': 'Street'})
        self.fields['billing_city'].widget.attrs.update({
            'placeholder': 'City'})
        self.fields['billing_state'].widget.attrs.update({
            'placeholder': 'State'})
        self.fields['billing_postcode'].widget.attrs.update({
            'placeholder': 'Postcode'})
        self.fields["billing_country"].choices = [
            ("", "--Country--"), ] + list(self.fields["billing_country"].choices)[1:]
        # self.fields["lead"].queryset = Lead.objects.all(
        # ).exclude(status='closed')
        if request_user.role == 'ADMIN':
            self.fields["lead"].queryset = Lead.objects.filter().exclude(
                status='closed')
            self.fields["contacts"].queryset = Contact.objects.filter()
            self.fields["teams"].choices = [(team.get('id'), team.get('name')) for team in Teams.objects.all().values('id', 'name')]
            self.fields["teams"].required = False
        else:
            self.fields["lead"].queryset = Lead.objects.filter(
                Q(assigned_to__in=[request_user]) | Q(created_by=request_user)).exclude(status='closed')
            self.fields["contacts"].queryset = Contact.objects.filter(
                Q(assigned_to__in=[request_user]) | Q(created_by=request_user))
            self.fields["teams"].required = False

        self.fields['assigned_to'].required = False
        if account_view:
            self.fields['billing_address_line'].required = True
            self.fields['billing_street'].required = True
            self.fields['billing_city'].required = True
            self.fields['billing_state'].required = True
            self.fields['billing_postcode'].required = True
            self.fields['billing_country'].required = True

        # lead is not mandatory while editing
        if self.instance.id:
            self.fields['lead'].required = False

    class Meta:
        model = Account
        fields = ('name', 'phone', 'email', 'website', 'industry',
                  'description', 'status', 'assigned_to',
                  'billing_address_line', 'billing_street',
                  'billing_city', 'billing_state',
                  'billing_postcode', 'billing_country', 'lead', 'contacts')


class AccountCommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'account', 'commented_by')


class AccountAttachmentForm(forms.ModelForm):
    attachment = forms.FileField(max_length=1001, required=True)

    class Meta:
        model = Attachments
        fields = ('attachment', 'account')


class EmailForm(forms.Form):
    recipients = forms.CharField(max_length=500)
    message_subject = forms.CharField(max_length=500)
    message_body = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(EmailForm, self).__init__(*args, **kwargs)
        self.fields['message_subject'].widget.attrs['class'] = 'form-control'
        self.fields['message_subject'].widget.attrs['required'] = True
        self.fields['message_subject'].widget.attrs['placeholder'] = 'Email Subject'
