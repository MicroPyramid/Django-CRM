from django import forms
from leads.models import Lead
from common.models import Comment, Attachments


class LeadForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        assigned_users = kwargs.pop('assigned_to', [])
        super(LeadForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        if self.data.get('status') == 'converted':
            self.fields['account_name'].required = True
            self.fields['email'].required = True
        self.fields['assigned_to'].queryset = assigned_users
        self.fields['assigned_to'].required = False
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False
        self.fields['title'].required = True
        for key, value in self.fields.items():
            if key == 'phone':
                value.widget.attrs['placeholder'] =\
                    'Enter phone number with country code'
            else:
                value.widget.attrs['placeholder'] = value.label

        self.fields['first_name'].widget.attrs.update({
            'placeholder': 'First Name'})
        self.fields['last_name'].widget.attrs.update({
            'placeholder': 'Last Name'})
        self.fields['account_name'].widget.attrs.update({
            'placeholder': 'Account Name'})
        self.fields['phone'].widget.attrs.update({
            'placeholder': '+91-123-456-7890'})
        self.fields['description'].widget.attrs.update({
            'rows': '6'})
        self.fields['address_line'].widget.attrs.update({
            'placeholder': 'Address Line'})
        self.fields['street'].widget.attrs.update({
            'placeholder': 'Street'})
        self.fields['city'].widget.attrs.update({
            'placeholder': 'City'})
        self.fields['state'].widget.attrs.update({
            'placeholder': 'State'})
        self.fields['postcode'].widget.attrs.update({
            'placeholder': 'Postcode'})
        self.fields["country"].choices = [
            ("", "--Country--"), ] + list(self.fields["country"].choices)[1:]

    class Meta:
        model = Lead
        fields = ('assigned_to', 'first_name',
                  'last_name', 'account_name', 'title',
                  'phone', 'email', 'status', 'source',
                  'website', 'description',
                  'address_line', 'street',
                  'city', 'state', 'postcode', 'country'
                  )


class LeadCommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'lead', 'commented_by')


class LeadAttachmentForm(forms.ModelForm):
    attachment = forms.FileField(max_length=1001, required=True)

    class Meta:
        model = Attachments
        fields = ('attachment', 'lead')
