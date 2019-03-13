import csv
import re
import json
import openpyxl
from django import forms

from common.models import User
from marketing.models import (
    ContactList, Contact,
    EmailTemplate, Campaign, Tag
)


def csv_doc_validate(document):
    temp_row = []
    reader = csv.reader((document.read().decode("utf-8")).splitlines())
    # csv_headers = ["first name", "last name", "email"]
    csv_headers = ["first name", "email"]
    # required_headers = ["first name", "last name", "email"]
    required_headers = ["first name", "email"]
    for y_index, row in enumerate(reader):
        each = {}
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
                        message = 'Missing required value %s for row %s' % (
                            csv_headers[x_index], y_index + 1)
                        return {"error": True, "message": message}
                each[csv_headers[x_index]] = cell_value
        temp_row.append(each)
    return {"error": False, "validated_rows": temp_row}


def get_validated_rows(wb, sheet_name, validated_rows):
    # headers = ["first name", "last name", "email"]
    # required_headers = ["first name", "last name", "email"]
    headers = ["first name", "email"]
    required_headers = ["first name", "email"]
    work_sheet = wb.get_sheet_by_name(name=sheet_name)
    for y_index, row in enumerate(work_sheet.iter_rows()):
        if y_index == 0:
            missing_headers = set(required_headers) - \
                set([str(cell.value).lower() for cell in row])
            if missing_headers:
                missing_headers_str = ', '.join(missing_headers)
                message = "Missing headers: %s %s" % (
                    missing_headers_str, sheet_name)
                return {"error": True, "message": message}
            continue
        elif not ''.join(str(cell.value) for cell in row):
            continue
        else:
            temp_row = []
            for x_index, cell in enumerate(row):
                try:
                    headers[x_index]
                except IndexError:
                    continue
                if headers[x_index] in required_headers:
                    if not cell.value:
                        message = 'Missing required \
                                    value %s for row %s in sheet %s'\
                            % (headers[x_index], y_index + 1, sheet_name)
                        return {"error": True, "message": message}
                    # elif x_index == 0:
                    #     cell_value = is_valid_date_format(cell.value)
                    #     if not cell_value:
                    #         message = 'Invalid date format(format:yyyy-mm-dd) \
                    #                  %s for row %s in sheet %s' % (headers[x_index], y_index + 1, sheet_name)
                    #         return {"error": True, "message": message}
                temp_row.append(cell.value)
            if len(temp_row) >= len(required_headers):
                validated_rows.append(temp_row)
    return validated_rows


def xls_doc_validate(document):
    wb = openpyxl.load_workbook(document)
    sheets = wb.get_sheet_names()
    validated_rows = []
    for sheet_name in sheets:
        get_validated_rows(wb, sheet_name, validated_rows)
    return {"error": False, "validated_rows": validated_rows}


def import_document_validator(document):
    try:
        # dialect = csv.Sniffer().sniff(document.read(1024).decode("ascii"))
        document.seek(0, 0)
        return csv_doc_validate(document)
    except Exception as e:
        print (e)
        try:
            return xls_doc_validate(document)
        except Exception as e:
            print (e)
            return {"error": True, "message": "Not a valid CSV/XLS file"}


class ContactListForm(forms.ModelForm):
    tags = forms.CharField(max_length=5000, required=False)
    contacts_file = forms.FileField(required=False)

    class Meta:
        model = ContactList
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super(ContactListForm, self).__init__(*args, **kwargs)
        self.fields['contacts_file'].widget.attrs.update({
            "accept": ".csv,.xls,.xlsx,.xlsm,.xlsb,.xml",
        })
        if self.instance is None:
            self.fields['contacts_file'].required = True
        if self.data.get('contacts_file'):
            self.fields['contacts_file'].widget.attrs.update({
                "accept": ".csv,.xls,.xlsx,.xlsm,.xlsb,.xml",
            })

    def clean_contacts_file(self):
        document = self.cleaned_data.get("contacts_file")
        if document:
            data = import_document_validator(document)
            if data.get("error"):
                raise forms.ValidationError(data.get("message"))
            else:
                self.validated_rows = data.get("validated_rows")
        return document

    def clean_tags(self):
        tags_data = self.data['tags'].split(",") if self.data['tags'] else []
        if len(tags_data) > 0:
            instance_tags = []
            if self.instance and self.instance.id is not None:
                instance_tags = list(
                    set(self.instance.tags.all().values_list(
                        'name', flat=True)))
            for each in tags_data:
                tags = Tag.objects.filter(name__iexact=each)
                if instance_tags:
                    tags = tags.exclude(name__in=instance_tags)
                if tags:
                    raise forms.ValidationError(
                        str(each) + ' Tag aleady existed with this name')
                if bool(re.search(r"[~\!_.@#\$%\^&\*\(\)\+{}\":;'/\[\]]",
                                  each)):
                    raise forms.ValidationError(
                        "Tags Should not contain special \
                        charcters except hyphens")
            return self.data['tags']
        raise forms.ValidationError("Enter Any tags")

    def clean_visible_to(self):
        visible_to_data = json.loads(self.data['visible_to'])
        if len(visible_to_data) > 0:
            instance_visible_to = []
            if self.instance and self.instance.id is not None:
                instance_visible_to = list(
                    set(self.instance.visible_to.all().values_list(
                        'email', flat=True)))
            for each in visible_to_data:
                visible_to = User.objects.filter(email=each)
                if instance_visible_to:
                    visible_to = visible_to.exclude(
                        email__in=instance_visible_to)
                if visible_to:
                    raise forms.ValidationError(
                        str(each) + ' User aleady existed')
            return self.data['visible_to']
        raise forms.ValidationError("Select any of the users")


class ContactForm(forms.ModelForm):
    contact_list = forms.CharField(max_length=5000)

    class Meta:
        model = Contact
        fields = ["name", "email", "contact_number"]

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)

    def clean_contact_list(self):
        contact_list = self.cleaned_data.get("contact_list")
        if not contact_list or contact_list == '[]' or\
                json.loads(contact_list) == []:
            raise forms.ValidationError(
                "Please choose any of the Contact List")
        else:
            for each in json.loads(contact_list):
                if not ContactList.objects.filter(id=each).first():
                    raise forms.ValidationError(
                        "Please choose a valid Contact List")

        return contact_list


class ContactsCSVUploadForm(forms.Form):
    contacts_file = forms.FileField()
    contact_list = forms.CharField(max_length=5000)

    def __init__(self, *args, **kwargs):
        super(ContactsCSVUploadForm, self).__init__(*args, **kwargs)
        self.fields['contacts_file'].widget.attrs.update({
            "accept": ".csv,.xls,.xlsx,.xlsm,.xlsb,.xml",
        })

    def clean_contacts_file(self):
        document = self.cleaned_data.get("contacts_file")
        data = import_document_validator(document)
        if data.get("error"):
            raise forms.ValidationError(data.get("message"))
        else:
            self.validated_rows = data.get("validated_rows")
        return document

    def clean_contact_list(self):
        contact_list = self.cleaned_data.get("contact_list")
        if not contact_list or contact_list == '[]' or\
                json.loads(contact_list) == []:
            raise forms.ValidationError(
                "Please choose any of the Contact List")
        else:
            for each in json.loads(contact_list):
                if not ContactList.objects.filter(id=each).first():
                    raise forms.ValidationError(
                        "Please choose a valid Contact List")

        return contact_list


class EmailTemplateForm(forms.ModelForm):

    class Meta:
        model = EmailTemplate
        fields = ['title', 'subject', 'html']


class SendCampaignForm(forms.ModelForm):
    schedule_later = forms.BooleanField(required=False)
    reply_to_crm = forms.BooleanField(required=False)
    timezone = forms.CharField(max_length=500, required=False)
    schedule_date_time = forms.CharField(max_length=100, required=False)
    reply_to_email = forms.EmailField(max_length=100, required=False)
    from_email = forms.EmailField(max_length=100, required=True)
    from_name = forms.CharField(max_length=100, required=True)
    contact_list = forms.CharField(max_length=5000, required=True)

    class Meta:
        model = Campaign
        fields = ['title', 'subject', 'html', 'email_template']

    def __init__(self, *args, **kwargs):
        super(SendCampaignForm, self).__init__(*args, **kwargs)
        if self.data.get('schedule_later') and self.data['schedule_later'] == 'true':
            self.fields['timezone'].required = True
            self.fields['schedule_date_time'].required = True
        if not self.data.get('reply_to_crm'):
            self.fields['reply_to_email'].required = True

    def clean_contact_list(self):
        contact_list = self.cleaned_data.get("contact_list")
        if not contact_list or contact_list == '[]' or \
                json.loads(contact_list) == []:
            raise forms.ValidationError(
                "Please choose any of the Contact List")
        else:
            for each in json.loads(contact_list):
                if not ContactList.objects.filter(id=each).first():
                    raise forms.ValidationError(
                        "Please choose a valid Contact List")

        return contact_list
