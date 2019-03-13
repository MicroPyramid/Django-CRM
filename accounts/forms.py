from django import forms
from .models import Account
from common.models import Comment, Attachments
from leads.models import Lead
from contacts.models import Contact
from django.db.models import Q


class AccountForm(forms.ModelForm):

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
        self.fields["lead"].queryset = Lead.objects.all(
        ).exclude(status='closed')
        if request_user:
            self.fields["lead"].queryset = Lead.objects.filter(
                Q(assigned_to__in=[request_user]) | Q(created_by=request_user)).exclude(status='closed')
            self.fields["contacts"].queryset = Contact.objects.filter(
                Q(assigned_to__in=[request_user]) | Q(created_by=request_user))

        if account_view:
            self.fields['billing_address_line'].required = True
            self.fields['billing_street'].required = True
            self.fields['billing_city'].required = True
            self.fields['billing_state'].required = True
            self.fields['billing_postcode'].required = True
            self.fields['billing_country'].required = True

    class Meta:
        model = Account
        fields = ('name', 'phone', 'email', 'website', 'industry',
                  'description', 'status',
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
