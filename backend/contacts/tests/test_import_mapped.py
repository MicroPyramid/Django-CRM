"""Contacts import in column-matching mode (a `mapping` form field is sent).

The file can use any column names and be .csv or .xlsx. Rows that cannot
become a contact, or that already exist, are skipped with their original
cells; a bad optional value is dropped and the row is kept. Requests without
`mapping` keep the template-only behaviour pinned in test_import.py.
"""

import csv
import io
import json

import openpyxl
import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError

from common.import_mapping import guess_mapping
from conftest import rls_org
from contacts.models import Contact
from contacts.services.csv_import import (
    CONTACT_FIELDS,
    CONTACT_SYNONYMS,
    KNOWN_HEADERS,
    RowError,
)

PREVIEW = "/api/contacts/import/preview/"
COMMIT = "/api/contacts/import/commit/"
BOTH = [PREVIEW, COMMIT]

CONFLICT_MESSAGE = (
    "A contact was created concurrently that conflicts with this "
    "import (likely a duplicate email). Re-run preview and try again."
)


# The header row of Outlook's "Comma Separated Values" contacts export, in
# Outlook's order. Windows Excel and Outlook write it in cp1252.
OUTLOOK_HEADERS = [
    "Title",
    "First Name",
    "Middle Name",
    "Last Name",
    "Suffix",
    "Company",
    "Department",
    "Job Title",
    "Business Street",
    "Business Street 2",
    "Business Street 3",
    "Business City",
    "Business State",
    "Business Postal Code",
    "Business Country/Region",
    "Home Street",
    "Home Street 2",
    "Home Street 3",
    "Home City",
    "Home State",
    "Home Postal Code",
    "Home Country/Region",
    "Other Street",
    "Other Street 2",
    "Other Street 3",
    "Other City",
    "Other State",
    "Other Postal Code",
    "Other Country/Region",
    "Assistant's Phone",
    "Business Fax",
    "Business Phone",
    "Business Phone 2",
    "Callback",
    "Car Phone",
    "Company Main Phone",
    "Home Fax",
    "Home Phone",
    "Home Phone 2",
    "ISDN",
    "Mobile Phone",
    "Other Fax",
    "Other Phone",
    "Pager",
    "Primary Phone",
    "Radio Phone",
    "TTY/TDD Phone",
    "Telex",
    "Account",
    "Anniversary",
    "Assistant's Name",
    "Billing Information",
    "Birthday",
    "Business Address PO Box",
    "Categories",
    "Children",
    "Directory Server",
    "E-mail Address",
    "E-mail Type",
    "E-mail Display Name",
    "E-mail 2 Address",
    "E-mail 2 Type",
    "E-mail 2 Display Name",
    "E-mail 3 Address",
    "E-mail 3 Type",
    "E-mail 3 Display Name",
    "Gender",
    "Government ID Number",
    "Hobby",
    "Home Address PO Box",
    "Initials",
    "Internet Free Busy",
    "Keywords",
    "Language",
    "Location",
    "Manager's Name",
    "Mileage",
    "Notes",
    "Office Location",
    "Organizational ID Number",
    "Other Address PO Box",
    "Priority",
    "Private",
    "Profession",
    "Referred By",
    "Sensitivity",
    "Spouse",
    "User 1",
    "User 2",
    "User 3",
    "User 4",
    "Web Page",
]


@pytest.fixture(autouse=True)
def _fresh_throttle():
    cache.clear()
    yield
    cache.clear()


def _upload(name, data):
    return SimpleUploadedFile(name, data, content_type="application/octet-stream")


def _csv(rows, encoding="utf-8"):
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    return buf.getvalue().encode(encoding)


def _xlsx(rows):
    wb = openpyxl.Workbook()
    for row in rows:
        wb.active.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _post(client, url, data, mapping="auto", name="contacts.csv"):
    return client.post(
        url, {"file": _upload(name, data), "mapping": mapping}, format="multipart"
    )


def _fields(body):
    return [c["field"] for c in body["columns"]]


@pytest.fixture
def existing_contact(org_a, admin_user):
    return Contact.objects.create(
        first_name="Pat",
        last_name="Lee",
        email="pat@acme.test",
        phone="+1 (202) 555-1234",
        org=org_a,
        created_by=admin_user,
    )


@pytest.mark.django_db
class TestMatching:
    def test_auto_mapping_google_export(self, admin_client, admin_profile):
        data = _csv(
            [
                [
                    "First Name",
                    "Last Name",
                    "E-mail 1 - Value",
                    "Phone 1 - Value",
                    "Organization Name",
                ],
                [
                    "Ada",
                    "Lovelace",
                    "ada@x.com ::: ada@work.example",
                    "+44 20 7946 0000 ::: +44 7700 900000",
                    "Analytical",
                ],
                ["Grace", "Hopper", "grace@x.com", "", "Navy"],
            ]
        )
        response = _post(admin_client, PREVIEW, data)
        assert response.status_code == 200, response.json()
        body = response.json()
        assert body["columns"][2]["field"] == "email"
        assert _fields(body) == [
            "first_name",
            "last_name",
            "email",
            "phone",
            "organization",
        ]
        assert body["summary"] == {"total": 2, "valid": 2, "skipped": 0}
        assert (body["valid"][0]["email"], body["valid"][0]["phone"]) == (
            "ada@x.com",
            "+44 20 7946 0000",
        )

    def test_google_type_columns_are_not_guessed(self, admin_client, admin_profile):
        headers = [
            "First Name",
            "Middle Name",
            "Last Name",
            "E-mail 1 - Type",
            "E-mail 1 - Value",
            "Phone 1 - Type",
            "Phone 1 - Value",
            "Organization Name",
            "Organization Title",
            "Notes",
        ]
        row = ["Ada", "", "Byte", "* Work", "ada@x.com", "Mobile", "", "Acme", "", ""]
        body = _post(admin_client, PREVIEW, _csv([headers, row])).json()
        assert _fields(body) == [
            "first_name",
            None,
            "last_name",
            None,
            "email",
            None,
            "phone",
            "organization",
            "title",
            "description",
        ]

    def test_auto_mapping_outlook_cp1252(self, admin_client, admin_profile):
        values = {
            "Title": "Mr.",
            "First Name": "José",
            "Last Name": "O’Brien",
            "Company": "Café Ltd",
            "Department": "Sales",
            "Job Title": "Head of Sales",
            "Business Street": "1 Main St",
            "Business City": "Pune",
            "Business State": "Maharashtra",
            "Business Postal Code": "411001",
            "Business Country/Region": "India",
            "Business Phone": "+91 20 1234 5678",
            "Home Phone": "+91 20 8765 4321",
            "Mobile Phone": "+91 98765 43210",
            "Anniversary": "0/0/00",
            "Birthday": "0/0/00",
            "E-mail Address": "jose@x.com",
            "E-mail Type": "SMTP",
            "E-mail Display Name": "José O’Brien (jose@x.com)",
            "Gender": "Unspecified",
            "Initials": "J.O.",
            "Notes": "Met at the expo",
            "Priority": "Normal",
            "Private": "False",
            "Sensitivity": "Normal",
        }
        row = [values.get(header, "") for header in OUTLOOK_HEADERS]
        data = _csv([OUTLOOK_HEADERS, row], encoding="cp1252")

        preview = _post(admin_client, PREVIEW, data).json()
        guessed = dict(zip(OUTLOOK_HEADERS, _fields(preview)))
        assert guessed["Title"] is None
        assert guessed["Job Title"] == "title"
        assert guessed["Mobile Phone"] == "phone"
        assert {header: f for header, f in guessed.items() if f} == {
            "First Name": "first_name",
            "Last Name": "last_name",
            "Company": "organization",
            "Department": "department",
            "Job Title": "title",
            "Business Street": "address_line",
            "Business City": "city",
            "Business State": "state",
            "Business Postal Code": "postcode",
            "Business Country/Region": "country",
            "Mobile Phone": "phone",
            "E-mail Address": "email",
            "Notes": "description",
        }

        response = _post(admin_client, COMMIT, data)
        assert response.status_code == 200, response.json()
        assert response.json()["dropped"] == []
        contact = Contact.objects.get()
        assert (contact.first_name, contact.last_name, contact.organization) == (
            "José",
            "O’Brien",
            "Café Ltd",
        )
        assert (contact.title, contact.phone, contact.email) == (
            "Head of Sales",
            "+91 98765 43210",
            "jose@x.com",
        )
        assert (contact.city, contact.country) == ("Pune", "IN")

    def test_auto_mapping_hubspot_owner_not_guessed(self, admin_client, admin_profile):
        headers = [
            "First Name",
            "Last Name",
            "Email",
            "Phone Number",
            "Company Name",
            "Job Title",
            "City",
            "State/Region",
            "Country/Region",
            "Postal Code",
            "Street Address",
            "Website URL",
            "Lifecycle Stage",
            "Lead Status",
            "Contact owner",
        ]
        row = [
            "Ada",
            "Byte",
            "ada@x.com",
            "+1 202 555 0100",
            "Acme",
            "CTO",
            "Pune",
            "Maharashtra",
            "India",
            "411001",
            "1 Main St",
            "https://acme.example",
            "customer",
            "Open",
            "Priya Sharma",
        ]
        body = _post(admin_client, PREVIEW, _csv([headers, row])).json()
        mapping = dict(zip(headers, _fields(body)))
        assert mapping["Contact owner"] is None
        assert mapping == {
            "First Name": "first_name",
            "Last Name": "last_name",
            "Email": "email",
            "Phone Number": "phone",
            "Company Name": "organization",
            "Job Title": "title",
            "City": "city",
            "State/Region": "state",
            "Country/Region": "country",
            "Postal Code": "postcode",
            "Street Address": "address_line",
            "Website URL": None,
            "Lifecycle Stage": None,
            "Lead Status": None,
            "Contact owner": None,
        }
        assert body["summary"]["valid"] == 1
        assert body["valid"][0]["country"] == "IN"
        assert body["valid"][0]["assigned_ids"] == []

    def test_xlsx_name_mobile_company_email_id(self, admin_client, admin_profile):
        data = _xlsx(
            [
                ["Name", "Mobile", "Company", "Email ID"],
                ["Ramesh Kumar", 919876543210, "Acme Traders", "ramesh@x.com"],
            ]
        )
        response = _post(admin_client, PREVIEW, data, name="contacts.xlsx")
        assert response.status_code == 200, response.json()
        body = response.json()
        assert _fields(body) == ["full_name", "phone", "organization", "email"]
        row = body["valid"][0]
        assert (row["first_name"], row["last_name"], row["phone"]) == (
            "Ramesh",
            "Kumar",
            "919876543210",
        )
        assert (row["organization"], row["email"]) == ("Acme Traders", "ramesh@x.com")

    def test_unknown_columns_never_refuse(self, admin_client, admin_profile):
        data = _csv([["First Name", "Last Name", "Shoe size"], ["Ada", "Byte", "42"]])
        body = _post(admin_client, PREVIEW, data).json()
        assert body["columns"][2]["field"] is None
        assert body["summary"] == {"total": 1, "valid": 1, "skipped": 0}

    def test_explicit_mapping_is_used(self, admin_client, admin_profile):
        data = _csv([["Col A", "Col B"], ["Ada", "Byte"]])
        mapping = json.dumps({"0": "first_name", "1": "last_name"})
        body = _post(admin_client, PREVIEW, data, mapping=mapping).json()
        assert _fields(body) == ["first_name", "last_name"]
        assert body["summary"] == {"total": 1, "valid": 1, "skipped": 0}


@pytest.mark.django_db
class TestSkippedRows:
    def test_one_word_name_skipped(self, admin_client, admin_profile):
        data = _csv(
            [
                ["Name", "Email"],
                ["Ramesh", "ramesh@x.com"],
                ["Ada Lovelace", "ada@x.com"],
                ["Grace Hopper", "grace@x.com"],
            ]
        )
        preview = _post(admin_client, PREVIEW, data).json()
        assert [s["row"] for s in preview["skipped"]] == [1]
        assert preview["skipped"][0]["field"] in ("first_name", "last_name")

        response = _post(admin_client, COMMIT, data)
        assert response.status_code == 200, response.json()
        body = response.json()
        assert (body["error"], body["created"], len(body["ids"])) == (False, 2, 2)
        assert [s["row"] for s in body["skipped"]] == [1]
        assert body["dropped"] == []
        assert sorted(Contact.objects.values_list("email", flat=True)) == [
            "ada@x.com",
            "grace@x.com",
        ]

    def test_duplicates_skip(self, admin_client, admin_profile, existing_contact):
        data = _csv(
            [
                ["First Name", "Last Name", "Email", "Phone"],
                ["Ada", "Byte", "Ada@x.com", ""],
                ["Ada", "Twin", "ada@x.com", ""],
                ["Pat", "Other", "pat@acme.test", ""],
                ["Phone", "Person", "", "202-555-1234"],
            ]
        )
        body = _post(admin_client, PREVIEW, data).json()
        assert [v["row"] for v in body["valid"]] == [1]
        assert [(s["row"], s["field"]) for s in body["skipped"]] == [
            (2, "email"),
            (3, "email"),
            (4, "phone"),
        ]

    def test_skip_kind_tells_duplicates_from_rows(
        self, admin_client, admin_profile, existing_contact
    ):
        data = _csv(
            [
                ["First Name", "Last Name", "Email"],
                ["Pat", "Other", "pat@acme.test"],
                ["Ramesh", "", "ramesh@x.com"],
            ]
        )
        body = _post(admin_client, PREVIEW, data).json()
        assert [(s["row"], s["kind"]) for s in body["skipped"]] == [
            (1, "duplicate"),
            (2, "row"),
        ]

    def test_reimport_same_file_creates_nothing(self, admin_client, admin_profile):
        data = _csv(
            [
                ["Name", "Email", "Phone"],
                ["Ada Lovelace", "ada@x.com", ""],
                ["Grace Hopper", "", "+1 202 555 0199"],
                ["Alan Turing", "", ""],
            ]
        )
        first = _post(admin_client, COMMIT, data)
        assert first.status_code == 200, first.json()
        assert first.json()["created"] == 3
        count = Contact.objects.count()

        second = _post(admin_client, COMMIT, data)
        assert second.status_code == 400
        body = second.json()
        assert body["error"] is True
        assert body["message"] == "Nothing in this file can be imported."
        assert body["created"] == 0
        assert len(body["skipped"]) == 3
        assert Contact.objects.count() == count

    def test_reimport_with_unreadable_email_creates_nothing(
        self, admin_client, admin_profile
    ):
        # "n/a" is dropped, which leaves a name-only row; the name check must
        # still see the contact the first import created.
        data = _csv([["Name", "Email"], ["Alan Turing", "n/a"]])
        first = _post(admin_client, COMMIT, data)
        assert first.status_code == 200, first.json()
        assert first.json()["dropped"] == [{"field": "email", "count": 1}]

        second = _post(admin_client, COMMIT, data)
        assert second.status_code == 400, second.json()
        assert [s["field"] for s in second.json()["skipped"]] == ["first_name"]
        assert Contact.objects.count() == 1

    def test_skipped_row_carries_original_cells(self, admin_client, admin_profile):
        data = _csv([["Name", "Email", "Shoe size"], ["Ramesh", "ramesh@x.com", "42"]])
        body = _post(admin_client, PREVIEW, data).json()
        assert body["skipped"][0]["cells"] == ["Ramesh", "ramesh@x.com", "42"]


@pytest.mark.django_db
class TestDroppedValues:
    def test_bad_phone_dropped_row_kept(self, admin_client, admin_profile):
        data = _csv([["First Name", "Last Name", "Phone"], ["Ada", "Byte", "abc"]])
        preview = _post(admin_client, PREVIEW, data).json()
        assert preview["summary"] == {"total": 1, "valid": 1, "skipped": 0}
        assert preview["dropped"] == [{"field": "phone", "count": 1}]

        response = _post(admin_client, COMMIT, data)
        assert response.status_code == 200, response.json()
        assert response.json()["dropped"] == [{"field": "phone", "count": 1}]
        contact = Contact.objects.get()
        assert contact.first_name == "Ada"
        assert not contact.phone

    def test_country_name_mapped_to_code(self, admin_client, admin_profile):
        data = _csv(
            [
                ["First Name", "Last Name", "Email", "Country"],
                ["Ada", "Byte", "ada@x.com", "India"],
                ["Grace", "Hopper", "grace@x.com", "united kingdom"],
                ["Alan", "Turing", "alan@x.com", "Atlantis"],
                ["Joan", "Clarke", "joan@x.com", "in"],
            ]
        )
        body = _post(admin_client, PREVIEW, data).json()
        assert [v["country"] for v in body["valid"]] == ["IN", "GB", None, "IN"]
        assert body["dropped"] == [{"field": "country", "count": 1}]

    def test_assignee_resolves_only_in_own_org(
        self, admin_client, admin_profile, profile_b
    ):
        data = _csv(
            [
                ["First", "Last", "Owner email"],
                ["Ada", "Byte", "userb@test.com"],
                ["Grace", "Hopper", "admin@test.com"],
            ]
        )
        mapping = json.dumps(
            {"0": "first_name", "1": "last_name", "2": "assigned_emails"}
        )
        body = _post(admin_client, PREVIEW, data, mapping=mapping).json()
        assert [v["assigned_ids"] for v in body["valid"]] == [
            [],
            [str(admin_profile.id)],
        ]
        assert body["dropped"] == [{"field": "assigned_emails", "count": 1}]


@pytest.mark.django_db
class TestRefusals:
    @pytest.mark.parametrize("url", BOTH)
    @pytest.mark.parametrize("target", ["org", "created_by", "id"])
    def test_mapping_forbidden_target_400(
        self, admin_client, admin_profile, url, target
    ):
        data = _csv([["First Name", "Last Name"], ["Ada", "Byte"]])
        response = _post(admin_client, url, data, mapping=json.dumps({"0": target}))
        assert response.status_code == 400
        assert response.json() == {
            "error": True,
            "message": "The column choices include a field that cannot be imported.",
        }
        assert not Contact.objects.exists()

    @pytest.mark.parametrize("url", BOTH)
    def test_mapping_same_field_twice_400(self, admin_client, admin_profile, url):
        data = _csv([["A", "B", "C"], ["Ada", "Byte", "ada@x.com"]])
        mapping = json.dumps({"0": "first_name", "1": "email", "2": "email"})
        response = _post(admin_client, url, data, mapping=mapping)
        assert response.status_code == 400
        assert response.json() == {
            "error": True,
            "message": "Two columns are set to email; choose one.",
        }

    @pytest.mark.parametrize("url", BOTH)
    def test_xls_refused_400(self, admin_client, admin_profile, url):
        response = _post(
            admin_client, url, b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", name="contacts.xls"
        )
        assert response.status_code == 400
        assert response.json() == {
            "error": True,
            "message": "Save it as .xlsx or .csv and try again.",
        }

    @pytest.mark.parametrize("url", BOTH)
    def test_user_without_import_right_403(self, user_client, user_profile, url):
        assert user_profile.has_sales_access is False
        data = _csv([["First Name", "Last Name"], ["Ada", "Byte"]])
        response = _post(user_client, url, data)
        assert response.status_code == 403
        assert response.json() == {"error": True, "message": "Permission denied"}
        assert not Contact.objects.exists()

    def test_mapped_import_stays_in_own_org(
        self, admin_client, admin_profile, org_a, org_b, org_b_client
    ):
        data = _csv([["Name", "Email"], ["Ada Lovelace", "ada@x.com"]])
        response = _post(admin_client, COMMIT, data)
        assert response.status_code == 200, response.json()
        assert Contact.objects.filter(org=org_a).count() == 1
        with rls_org(org_b):
            assert Contact.objects.filter(org=org_b).count() == 0

        preview = _post(org_b_client, PREVIEW, data).json()
        assert preview["skipped"] == []
        assert preview["summary"] == {"total": 1, "valid": 1, "skipped": 0}

    def test_ragged_rows(self, admin_client, admin_profile):
        data = b"First Name,Last Name,Email\nAda,Byte,ada@x.com,\nBob,Smith\n"
        preview = _post(admin_client, PREVIEW, data).json()
        assert preview["summary"] == {"total": 2, "valid": 2, "skipped": 0}

        response = _post(admin_client, COMMIT, data)
        assert response.status_code == 200, response.json()
        assert response.json()["created"] == 2

    def test_integrity_error_reports_existing_message(
        self, admin_client, admin_profile, monkeypatch
    ):
        def _race(*args, **kwargs):
            raise IntegrityError("duplicate key")

        monkeypatch.setattr("contacts.services.csv_import._commit_validated", _race)
        data = _csv([["Name", "Email"], ["Ada Lovelace", "ada@x.com"]])
        response = _post(admin_client, COMMIT, data)
        assert response.status_code == 400
        assert response.json() == {
            "error": True,
            "message": CONFLICT_MESSAGE,
            "created": 0,
        }


@pytest.mark.django_db
class TestLegacyMode:
    def test_without_mapping_is_legacy(self, admin_client, admin_profile):
        data = _csv(
            [["first_name", "last_name", "email"], ["Ada", "Byte", "ada@x.com"]]
        )
        response = admin_client.post(
            PREVIEW, {"file": _upload("contacts.csv", data)}, format="multipart"
        )
        assert response.status_code == 200, response.json()
        body = response.json()
        assert "header_error" in body and "errors" in body
        assert "columns" not in body
        assert body["summary"] == {"total": 1, "valid": 1, "invalid": 0}


class TestTables:
    def test_fields_are_the_template_plus_full_name(self):
        names = [name for name, _label, _required in CONTACT_FIELDS]
        assert names == [*KNOWN_HEADERS, "full_name"]
        assert {name for name, _label, required in CONTACT_FIELDS if required} == {
            "first_name",
            "last_name",
        }

    def test_template_headers_guess_themselves(self):
        assert guess_mapping(list(KNOWN_HEADERS), CONTACT_SYNONYMS) == list(
            KNOWN_HEADERS
        )

    def test_every_synonym_target_is_importable(self):
        names = {name for name, _label, _required in CONTACT_FIELDS}
        assert set(CONTACT_SYNONYMS) <= names

    def test_row_error_kind_is_not_serialized(self):
        error = RowError(3, "email", "Duplicate", kind="duplicate")
        assert error.to_dict() == {"row": 3, "field": "email", "message": "Duplicate"}
        assert RowError(3, "phone", "Bad").kind == "value"
