from django import forms
from invoices.models import Invoice
from common.models import User, Comment, Attachments, Address
from django.db.models import Q
from teams.models import Teams
from accounts.models import Account


class InvoiceForm(forms.ModelForm):
    teams_queryset = []
    teams = forms.MultipleChoiceField(choices=teams_queryset)

    def __init__(self, *args, **kwargs):
        request_user = kwargs.pop('request_user', None)
        assigned_users = kwargs.pop('assigned_to', [])
        super(InvoiceForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
            field.required = False

        if request_user.role == 'ADMIN' or request_user.is_superuser:
            self.fields['assigned_to'].queryset = User.objects.filter(
                is_active=True)
            self.fields["teams"].choices = [(team.get('id'), team.get(
                'name')) for team in Teams.objects.all().values('id', 'name')]
            self.fields['accounts'].queryset = Account.objects.filter(
                status='open')
        # elif request_user.google.all():
        #     self.fields['assigned_to'].queryset = User.objects.none()
        #     self.fields['accounts'].queryset = Account.objects.filter(status='open').filter(
        #         Q(created_by=request_user) | Q(assigned_to=request_user))
        elif request_user.role == 'USER':
            self.fields['assigned_to'].queryset = User.objects.filter(
                role='ADMIN')
            self.fields['accounts'].queryset = Account.objects.filter(status='open').filter(
                Q(created_by=request_user) | Q(assigned_to=request_user))
        else:
            pass

        self.fields["teams"].required = False
        self.fields['phone'].widget.attrs.update({
            'placeholder': '+91-123-456-7890'})
        self.fields['invoice_title'].required = True
        self.fields['invoice_number'].required = True
        self.fields['currency'].required = True
        self.fields['email'].required = True
        self.fields['total_amount'].required = True
        self.fields['due_date'].required = True
        self.fields['accounts'].required = False

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')

        if quantity in [None, '']:
            raise forms.ValidationError('This field is required')

        return quantity

    def clean_invoice_number(self):
        invoice_number = self.cleaned_data.get('invoice_number')
        if Invoice.objects.filter(invoice_number=invoice_number).exclude(id=self.instance.id).exists():
            raise forms.ValidationError(
                'Invoice with this Invoice Number already exists.')

        return invoice_number

    class Meta:
        model = Invoice
        fields = ('invoice_title', 'invoice_number',
                  'from_address', 'to_address', 'name',
                  'email', 'phone', 'status', 'assigned_to',
                  'quantity', 'rate', 'total_amount',
                  'currency', 'details', 'due_date', 'accounts'
                  )


class InvoiceCommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=255, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'task', 'commented_by')


class InvoiceAttachmentForm(forms.ModelForm):
    attachment = forms.FileField(max_length=1001, required=True)

    class Meta:
        model = Attachments
        fields = ('attachment', 'task')


class InvoiceAddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('address_line', 'street', 'city',
                  'state', 'postcode', 'country')

    def __init__(self, *args, **kwargs):
        super(InvoiceAddressForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
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
