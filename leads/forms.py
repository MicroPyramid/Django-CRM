import csv
import json
import re

import openpyxl
from django import forms

from common.models import Attachments, Comment
from leads.models import Lead
from phonenumber_field.formfields import PhoneNumberField
from teams.models import Teams


class LeadForm(forms.ModelForm):
    teams_queryset = []
    teams = forms.MultipleChoiceField(choices=teams_queryset)

    def __init__(self, *args, **kwargs):
        assigned_users = kwargs.pop('assigned_to', [])
        super(LeadForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        if self.data.get('status') == 'converted':
            self.fields['account_name'].required = True
            self.fields['email'].required = True
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False
        self.fields['title'].required = True
        if assigned_users:
            self.fields['assigned_to'].queryset = assigned_users
        self.fields['assigned_to'].required = False
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
        self.fields["teams"].choices = [(team.get('id'), team.get('name')) for team in Teams.objects.all().values('id', 'name')]
        self.fields["teams"].required = False

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
    comment = forms.CharField(max_length=255, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'lead', 'commented_by')


class LeadAttachmentForm(forms.ModelForm):
    attachment = forms.FileField(max_length=1001, required=True)

    class Meta:
        model = Attachments
        fields = ('attachment', 'lead')

email_regex = '^[_a-zA-Z0-9-]+(\.[_a-zA-Z0-9-]+)*@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*(\.[a-zA-Z]{2,4})$'

def csv_doc_validate(document):
    temp_row = []
    invalid_row = []
    # this stores all the failed csv contacts
    failed_leads_csv = []
    reader = csv.reader((document.read().decode("iso-8859-1")).splitlines())
    # csv_headers = ["first name", "last name", "email"]
    csv_headers = ["title"]
    # required_headers = ["first name", "last name", "email"]
    required_headers = ["title"]
    for y_index, row in enumerate(reader):
        each = {}
        invalid_each = {}
        if y_index == 0:
            csv_headers = [header_name.lower()
                           for header_name in row if header_name]
            missing_headers = set(required_headers) - \
                set([r.lower() for r in row])
            if missing_headers:
                missing_headers_str = ', '.join(missing_headers)
                message = 'Missing headers: %s' % (missing_headers_str)
                return {"error": True, "message": message}
            continue
        elif not ''.join(str(x) for x in row):
            continue
        else:
            for x_index, cell_value in enumerate(row):
                try:
                    csv_headers[x_index]
                except IndexError:
                    continue
                if csv_headers[x_index] in required_headers:
                    if not cell_value:
                        # message = 'Missing required value %s for row %s' % (
                        #     csv_headers[x_index], y_index + 1)
                        # return {"error": True, "message": message}
                        invalid_each[csv_headers[x_index]] = cell_value
                    else:
                        if csv_headers[x_index] == "email":
                            if re.match(email_regex, cell_value) is None:
                                invalid_each[csv_headers[x_index]] = cell_value
                each[csv_headers[x_index]] = cell_value
        if invalid_each:
            invalid_row.append(each)
            failed_leads_csv.append(list(each.values()))
        else:
            temp_row.append(each)
    return {"error": False, "validated_rows": temp_row, "invalid_rows": invalid_row, "headers":csv_headers,
        "failed_leads_csv": failed_leads_csv}

def import_document_validator(document):
    try:
        # dialect = csv.Sniffer().sniff(document.read(1024).decode("ascii"))
        document.seek(0, 0)
        return csv_doc_validate(document)
    except Exception as e:
        print(e)
        return {"error": True, "message": "Not a valid CSV file"}


class LeadListForm(forms.Form):
    leads_file = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        super(LeadListForm, self).__init__(*args, **kwargs)
        self.fields['leads_file'].widget.attrs.update({
            "accept": ".csv",
        })
        self.fields['leads_file'].required = True
        if self.data.get('leads_file'):
            self.fields['leads_file'].widget.attrs.update({
                "accept": ".csv",
            })

    def clean_leads_file(self):
        document = self.cleaned_data.get("leads_file")
        if document:
            data = import_document_validator(document)
            if data.get("error"):
                raise forms.ValidationError(data.get("message"))
            else:
                self.validated_rows = data.get("validated_rows", [])
                self.invalid_rows = data.get("invalid_rows", [])
                if len(self.validated_rows) == 0:
                    raise forms.ValidationError("All the leads in the file are invalid.")
        return document
