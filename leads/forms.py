import csv
import re

from django import forms

email_regex = "^[_a-zA-Z0-9-]+(\.[_a-zA-Z0-9-]+)*@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*(\.[a-zA-Z]{2,4})$"


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
            csv_headers = [header_name.lower() for header_name in row if header_name]
            missing_headers = set(required_headers) - set([r.lower() for r in row])
            if missing_headers:
                missing_headers_str = ", ".join(missing_headers)
                message = "Missing headers: %s" % (missing_headers_str)
                return {"error": True, "message": message}
            continue
        elif not "".join(str(x) for x in row):
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
    return {
        "error": False,
        "validated_rows": temp_row,
        "invalid_rows": invalid_row,
        "headers": csv_headers,
        "failed_leads_csv": failed_leads_csv,
    }


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
        super().__init__(*args, **kwargs)
        self.fields["leads_file"].widget.attrs.update(
            {
                "accept": ".csv",
            }
        )
        self.fields["leads_file"].required = True
        if self.data.get("leads_file"):
            self.fields["leads_file"].widget.attrs.update(
                {
                    "accept": ".csv",
                }
            )

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
                    raise forms.ValidationError(
                        "All the leads in the file are invalid."
                    )
        return document
