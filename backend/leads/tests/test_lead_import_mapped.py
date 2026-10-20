"""Leads import in column-matching mode (a `mapping` form field is sent).

The file can use any column names and be .csv or .xlsx. A row with no name,
or that duplicates a lead (by email, phone, or name when it has neither), is
skipped with its original cells; a bad optional value is dropped and the row
is kept. Requests without `mapping` keep the template-only behaviour pinned in
test_lead_import.py.
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
from common.models import CustomFieldDefinition
from common.permissions import is_org_admin
from conftest import rls_org
from leads.access import visible_leads_qs
from leads.csv_import import KNOWN_HEADERS, LEAD_FIELDS, LEAD_SYNONYMS
from leads.models import Lead

PREVIEW = "/api/leads/import/preview/"
COMMIT = "/api/leads/import/commit/"
BOTH = [PREVIEW, COMMIT]

CONFLICT_MESSAGE = (
    "A lead was created at the same time that conflicts with this "
    "import (likely a duplicate email). Run the preview again."
)
PHONE_EXISTS = "A lead with this phone number already exists in your organization"
NAME_EXISTS = (
    "A lead with this name already exists; add an email or phone to confirm "
    "it's a different person"
)
PERSON_HEADERS = ["First Name", "Last Name", "Email", "Phone"]

# HubSpot's published contact and lead export header row.
HUBSPOT_HEADERS = [
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


def _post(client, url, data, mapping="auto", name="leads.csv"):
    return client.post(
        url, {"file": _upload(name, data), "mapping": mapping}, format="multipart"
    )


def _fields(body):
    return [c["field"] for c in body["columns"]]


@pytest.mark.django_db
class TestMatching:
    def test_auto_mapping_hubspot_export(self, admin_client, admin_profile):
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
            "lead",
            "New",
            "Priya Sharma",
        ]
        body = _post(admin_client, PREVIEW, _csv([HUBSPOT_HEADERS, row])).json()
        mapping = dict(zip(HUBSPOT_HEADERS, _fields(body)))
        assert mapping["Company Name"] == "company_name"
        assert mapping["Lead Status"] == "status"
        # The owner column holds a person's name, never an email to assign by.
        assert mapping["Contact owner"] is None
        assert mapping == {
            "First Name": "first_name",
            "Last Name": "last_name",
            "Email": "email",
            "Phone Number": "phone",
            "Company Name": "company_name",
            "Job Title": "job_title",
            "City": "city",
            "State/Region": "state",
            "Country/Region": "country",
            "Postal Code": "postcode",
            "Street Address": "address_line",
            "Website URL": "website",
            "Lifecycle Stage": None,
            "Lead Status": "status",
            "Contact owner": None,
        }
        assert body["summary"] == {"total": 1, "valid": 1, "skipped": 0}
        # HubSpot's "New" is not one of our statuses: dropped and counted.
        assert body["dropped"] == [{"field": "status", "count": 1}]
        valid = body["valid"][0]
        assert (valid["company_name"], valid["status"]) == ("Acme", None)
        assert valid["assigned_ids"] == []

    def test_title_is_the_lead_title_and_salutation_has_its_own_names(self):
        headers = ["Title", "Job Title", "Prefix", "Subject"]
        assert guess_mapping(headers, LEAD_SYNONYMS) == [
            None,
            "job_title",
            "salutation",
            "title",
        ]
        assert guess_mapping(["Title", "Salutation"], LEAD_SYNONYMS) == [
            "title",
            "salutation",
        ]

    def test_explicit_mapping_is_used(self, admin_client, admin_profile):
        data = _csv([["Col A", "Col B"], ["Ada", "Big deal"]])
        mapping = json.dumps({"0": "first_name", "1": "title"})
        body = _post(admin_client, PREVIEW, data, mapping=mapping).json()
        assert _fields(body) == ["first_name", "title"]
        assert body["valid"][0]["title"] == "Big deal"


@pytest.mark.django_db
class TestAcceptedRows:
    def test_lead_name_header_is_the_person(self, admin_client, admin_profile):
        data = _csv([["Lead Name", "Email"], ["Ada Byte", "ada@x.com"]])
        body = _post(admin_client, PREVIEW, data).json()
        assert _fields(body) == ["full_name", "email"]
        assert body["summary"] == {"total": 1, "valid": 1, "skipped": 0}
        row = body["valid"][0]
        assert (row["first_name"], row["last_name"], row["title"]) == (
            "Ada",
            "Byte",
            None,
        )

    def test_one_word_name_is_a_lead(self, admin_client, admin_profile, org_a):
        data = _xlsx(
            [
                ["Name", "Mobile", "Company", "Email ID"],
                ["Ramesh", 919876543210, "Acme Traders", "ramesh@x.com"],
            ]
        )
        preview = _post(admin_client, PREVIEW, data, name="leads.xlsx").json()
        assert _fields(preview) == ["full_name", "phone", "company_name", "email"]
        assert preview["summary"] == {"total": 1, "valid": 1, "skipped": 0}
        row = preview["valid"][0]
        assert (row["first_name"], row["last_name"]) == ("Ramesh", None)
        assert row["company_name"] == "Acme Traders"

        response = _post(admin_client, COMMIT, data, name="leads.xlsx")
        assert response.status_code == 200, response.json()
        lead = Lead.objects.get()
        assert (lead.first_name, lead.phone, lead.org_id) == (
            "Ramesh",
            "919876543210",
            org_a.id,
        )


@pytest.mark.django_db
class TestSkippedRows:
    def test_row_without_any_name_skipped(self, admin_client, admin_profile):
        data = _csv(
            [
                ["First Name", "Last Name", "Email", "Company"],
                ["", "", "nobody@x.com", "Acme"],
                ["Ada", "", "ada@x.com", "Acme"],
                ["", "Hopper", "grace@x.com", ""],
            ]
        )
        preview = _post(admin_client, PREVIEW, data).json()
        assert [s["row"] for s in preview["skipped"]] == [1]
        assert "name" in preview["skipped"][0]["message"]

        response = _post(admin_client, COMMIT, data)
        assert response.status_code == 200, response.json()
        body = response.json()
        assert (body["error"], body["created"]) == (False, 2)
        assert [s["row"] for s in body["skipped"]] == [1]
        assert sorted(Lead.objects.values_list("email", flat=True)) == [
            "ada@x.com",
            "grace@x.com",
        ]

    def test_duplicate_email_case_insensitive_skipped(
        self, admin_client, admin_profile, admin_user, org_a
    ):
        Lead.objects.create(
            first_name="Pat", email="pat@acme.test", org=org_a, created_by=admin_user
        )
        data = _csv(
            [
                ["First Name", "Last Name", "Email"],
                ["Ada", "Byte", "Ada@x.com"],
                ["Ada", "Twin", "ada@X.com"],
                ["Pat", "Other", "PAT@acme.test"],
                ["Grace", "Hopper", "grace@x.com"],
            ]
        )
        body = _post(admin_client, PREVIEW, data).json()
        assert [v["row"] for v in body["valid"]] == [1, 4]
        assert [(s["row"], s["field"]) for s in body["skipped"]] == [
            (2, "email"),
            (3, "email"),
        ]
        assert body["dropped"] == []

    def test_duplicate_email_case_mapping_mismatch_is_skipped(
        self, admin_client, admin_profile, admin_user, org_a
    ):
        # Python's lower() and the database's LOWER() can disagree outside
        # ASCII (SQLite's is ASCII-only), so the bulk pre-check can miss this.
        # The create serializer's own check still finds it, and the row must
        # be skipped as a duplicate, not imported with its email dropped.
        Lead.objects.create(
            first_name="Pat", email="pat@ÜBER.de", org=org_a, created_by=admin_user
        )
        data = _csv(
            [["First Name", "Last Name", "Email"], ["Pat", "Two", "pat@ÜBER.de"]]
        )
        body = _post(admin_client, PREVIEW, data).json()
        assert body["summary"] == {"total": 1, "valid": 0, "skipped": 1}
        assert [(s["row"], s["field"]) for s in body["skipped"]] == [(1, "email")]
        assert body["skipped"][0]["message"] == "A lead with this email already exists"
        assert body["dropped"] == []

    def test_skip_kind_tells_duplicates_from_rows(
        self, admin_client, admin_profile, admin_user, org_a
    ):
        Lead.objects.create(
            first_name="Pat", email="pat@acme.test", org=org_a, created_by=admin_user
        )
        data = _csv(
            [
                ["First Name", "Last Name", "Email"],
                ["Pat", "Other", "pat@acme.test"],
                ["", "", "nobody@x.com"],
                ["Ada", "Byte", "ada@x.com"],
                ["Ada", "Twin", "ADA@x.com"],
            ]
        )
        body = _post(admin_client, PREVIEW, data).json()
        assert [(s["row"], s["kind"]) for s in body["skipped"]] == [
            (1, "duplicate"),
            (2, "row"),
            (4, "duplicate"),
        ]

    def test_reimport_same_file_creates_nothing(self, admin_client, admin_profile):
        data = _csv(
            [
                ["Name", "Email", "Lead Status"],
                ["Ada Lovelace", "ada@x.com", "Assigned"],
                ["Grace Hopper", "grace@x.com", ""],
                ["Alan Turing", "alan@x.com", "in process"],
            ]
        )
        first = _post(admin_client, COMMIT, data)
        assert first.status_code == 200, first.json()
        assert first.json()["created"] == 3
        count = Lead.objects.count()

        second = _post(admin_client, COMMIT, data)
        assert second.status_code == 400
        body = second.json()
        assert body["error"] is True
        assert body["message"] == "Nothing in this file can be imported."
        assert body["created"] == 0
        assert len(body["skipped"]) == 3
        assert Lead.objects.count() == count

    def test_skipped_row_carries_original_cells(self, admin_client, admin_profile):
        data = _csv([["Name", "Company", "Shoe size"], ["", "Acme", "42"]])
        body = _post(admin_client, PREVIEW, data).json()
        assert body["skipped"][0]["cells"] == ["", "Acme", "42"]


def _skips(body):
    return [(s["row"], s["field"], s["message"], s["kind"]) for s in body["skipped"]]


@pytest.mark.django_db
class TestPhoneAndNameDuplicates:
    """The contacts rules, applied to leads: phone always, and first and last
    name only for a row left with no email and no phone. Both are matched
    among the leads the importer can see, never across the whole org."""

    def test_phone_duplicate_within_file_skipped(self, admin_client, admin_profile):
        data = _csv(
            [
                PERSON_HEADERS,
                ["Ada", "Byte", "", "+1 (202) 555-0100"],
                ["Grace", "Hopper", "", "202.555.0100"],
                ["Alan", "Turing", "", "202 555 0199"],
            ]
        )
        body = _post(admin_client, PREVIEW, data).json()
        assert [v["row"] for v in body["valid"]] == [1, 3]
        assert _skips(body) == [
            (
                2,
                "phone",
                "Duplicate phone number also used by row 1 in this file",
                "duplicate",
            )
        ]

    def test_phone_of_visible_lead_skipped(
        self, admin_client, admin_profile, admin_user, org_a
    ):
        Lead.objects.create(
            first_name="Pat", phone="+91 20 2555 0100", org=org_a, created_by=admin_user
        )
        data = _csv([PERSON_HEADERS, ["New", "Person", "new@x.com", "2025550100"]])
        body = _post(admin_client, PREVIEW, data).json()
        assert body["summary"] == {"total": 1, "valid": 0, "skipped": 1}
        assert _skips(body) == [(1, "phone", PHONE_EXISTS, "duplicate")]

    def test_name_duplicate_without_email_or_phone_skipped(
        self, admin_client, admin_profile, admin_user, org_a
    ):
        Lead.objects.create(
            first_name="Ada", last_name="Byte", org=org_a, created_by=admin_user
        )
        data = _csv(
            [
                PERSON_HEADERS,
                ["ada", "BYTE", "", ""],
                ["Grace", "Hopper", "", ""],
                ["GRACE", "hopper", "", ""],
                ["Ramesh", "", "", ""],
                ["ramesh", "", "", ""],
            ]
        )
        body = _post(admin_client, PREVIEW, data).json()
        assert [v["row"] for v in body["valid"]] == [2, 4]
        same_name = (
            "Same name as row {} in this file; add an email or phone to either "
            "row to confirm they're different people"
        )
        assert _skips(body) == [
            (1, "first_name", NAME_EXISTS, "duplicate"),
            (3, "first_name", same_name.format(2), "duplicate"),
            (5, "first_name", same_name.format(4), "duplicate"),
        ]

    @pytest.mark.parametrize("stored_last_name", [None, ""])
    def test_one_word_name_matches_a_stored_lead_with_no_last_name(
        self, admin_client, admin_profile, admin_user, org_a, stored_last_name
    ):
        Lead.objects.create(
            first_name="Ramesh",
            last_name=stored_last_name,
            org=org_a,
            created_by=admin_user,
        )
        data = _csv(
            [PERSON_HEADERS, ["RAMESH", "", "", ""], ["Ramesh", "Kumar", "", ""]]
        )
        body = _post(admin_client, PREVIEW, data).json()
        # Only the same single word matches; "Ramesh Kumar" is someone else.
        assert [v["row"] for v in body["valid"]] == [2]
        assert _skips(body) == [(1, "first_name", NAME_EXISTS, "duplicate")]

    def test_name_not_checked_when_email_or_phone_present(
        self, admin_client, admin_profile, admin_user, org_a
    ):
        Lead.objects.create(
            first_name="Ada", last_name="Byte", org=org_a, created_by=admin_user
        )
        data = _csv(
            [
                PERSON_HEADERS,
                ["Ada", "Byte", "ada@x.com", ""],
                ["Ada", "Byte", "", "202-555-0100"],
                ["Ada", "Byte", "ada2@x.com", "202-555-0199"],
                # One bad value dropped, one usable value kept: still no check.
                ["Ada", "Byte", "n/a", "202-555-0111"],
                ["Ada", "Byte", "ada3@x.com", "call me"],
            ]
        )
        body = _post(admin_client, PREVIEW, data).json()
        assert body["summary"] == {"total": 5, "valid": 5, "skipped": 0}
        assert body["dropped"] == [
            {"field": "email", "count": 1},
            {"field": "phone", "count": 1},
        ]

    @pytest.mark.parametrize(
        "email, phone", [("", "call me"), ("n/a", ""), ("n/a", "call me")]
    )
    def test_row_whose_bad_values_are_dropped_is_name_checked(
        self, admin_client, admin_profile, admin_user, org_a, email, phone
    ):
        Lead.objects.create(
            first_name="Ada", last_name="Byte", org=org_a, created_by=admin_user
        )
        data = _csv(
            [
                PERSON_HEADERS,
                ["Ada", "Byte", email, phone],
                ["Grace", "Hopper", "", ""],
                ["Grace", "Hopper", email, phone],
            ]
        )
        body = _post(admin_client, PREVIEW, data).json()
        assert [v["row"] for v in body["valid"]] == [2]
        assert _skips(body) == [
            (1, "first_name", NAME_EXISTS, "duplicate"),
            (
                3,
                "first_name",
                "Same name as row 2 in this file; add an email or phone to "
                "either row to confirm they're different people",
                "duplicate",
            ),
        ]
        # A skipped row's dropped values are not counted.
        assert body["dropped"] == []

    def test_hidden_lead_is_never_a_duplicate(
        self, user_client, user_profile, regular_user, admin_user, org_a
    ):
        """A sales member who cannot open a lead must not learn it exists
        from the preview: a phone or name held only by that lead imports."""
        user_profile.has_sales_access = True
        user_profile.save(update_fields=["has_sales_access"])
        assert not is_org_admin(user_profile)
        hidden = Lead.objects.create(
            first_name="Hidden",
            last_name="Person",
            phone="+1 (202) 555-0101",
            org=org_a,
            created_by=admin_user,
        )
        mine = Lead.objects.create(
            first_name="Mine",
            last_name="Visible",
            phone="+1 (202) 555-0202",
            org=org_a,
            created_by=regular_user,
        )
        visible = visible_leads_qs(user_profile)
        assert not visible.filter(pk=hidden.pk).exists()
        assert visible.filter(pk=mine.pk).exists()

        data = _csv(
            [
                PERSON_HEADERS,
                ["New", "Person", "", "202-555-0101"],
                ["hidden", "PERSON", "", ""],
                ["Other", "Person", "", "202-555-0202"],
                ["mine", "VISIBLE", "", ""],
            ]
        )
        body = _post(user_client, PREVIEW, data).json()
        assert [v["row"] for v in body["valid"]] == [1, 2]
        assert _skips(body) == [
            (3, "phone", PHONE_EXISTS, "duplicate"),
            (4, "first_name", NAME_EXISTS, "duplicate"),
        ]

    def test_other_org_lead_never_matches(
        self, admin_client, admin_profile, org_a, org_b
    ):
        with rls_org(org_b):
            Lead.objects.create(
                first_name="Bee", last_name="Lead", phone="202-555-0101", org=org_b
            )
        data = _csv(
            [
                PERSON_HEADERS,
                ["New", "Person", "", "+1 202 555 0101"],
                ["Bee", "Lead", "", ""],
            ]
        )
        body = _post(admin_client, PREVIEW, data).json()
        assert body["summary"] == {"total": 2, "valid": 2, "skipped": 0}

        response = _post(admin_client, COMMIT, data)
        assert response.status_code == 200, response.json()
        assert response.json()["created"] == 2
        assert Lead.objects.filter(org=org_a).count() == 2

    def test_reimport_phone_only_sheet_creates_nothing(
        self, admin_client, admin_profile, org_a
    ):
        data = _csv(
            [
                ["Name", "Phone", "Company"],
                ["Ada Lovelace", "+44 20 7946 0100", "Engines"],
                ["Grace Hopper", "(202) 555-0100", "Navy"],
                ["Ramesh", "919876543210", "Acme Traders"],
            ]
        )
        first = _post(admin_client, COMMIT, data)
        assert first.status_code == 200, first.json()
        assert first.json()["created"] == 3

        second = _post(admin_client, COMMIT, data)
        assert second.status_code == 400
        body = second.json()
        assert (body["error"], body["created"]) == (True, 0)
        assert body["message"] == "Nothing in this file can be imported."
        assert [(s["row"], s["field"], s["kind"]) for s in body["skipped"]] == [
            (1, "phone", "duplicate"),
            (2, "phone", "duplicate"),
            (3, "phone", "duplicate"),
        ]
        assert Lead.objects.filter(org=org_a).count() == 3


@pytest.mark.django_db
class TestDroppedValues:
    def test_unknown_status_dropped(self, admin_client, admin_profile):
        data = _csv(
            [["Name", "Email", "Status"], ["Ada Byte", "ada@x.com", "Hot prospect!!"]]
        )
        preview = _post(admin_client, PREVIEW, data).json()
        assert preview["summary"] == {"total": 1, "valid": 1, "skipped": 0}
        assert preview["dropped"] == [{"field": "status", "count": 1}]

        response = _post(admin_client, COMMIT, data)
        assert response.status_code == 200, response.json()
        assert response.json()["dropped"] == [{"field": "status", "count": 1}]
        lead = Lead.objects.get()
        assert lead.status == Lead._meta.get_field("status").get_default()

    @pytest.mark.parametrize("status", ["converted", "Converted"])
    def test_converted_status_dropped(self, admin_client, admin_profile, status):
        # No email on purpose: a "converted" status would also demand one.
        data = _csv([["Name", "Email", "Status"], ["Ada Byte", "", status]])
        preview = _post(admin_client, PREVIEW, data).json()
        assert preview["summary"] == {"total": 1, "valid": 1, "skipped": 0}
        assert preview["dropped"] == [{"field": "status", "count": 1}]

        response = _post(admin_client, COMMIT, data)
        assert response.status_code == 200, response.json()
        lead = Lead.objects.get()
        assert lead.status != "converted"

    def test_unresolved_assigned_email_dropped(
        self, admin_client, admin_profile, profile_b
    ):
        # userb@test.com is a user, but in another org.
        data = _csv(
            [
                ["First Name", "Last Name", "Assigned Emails"],
                ["Ada", "Byte", "userb@test.com"],
                ["Grace", "Hopper", "admin@test.com"],
            ]
        )
        preview = _post(admin_client, PREVIEW, data).json()
        assert preview["summary"] == {"total": 2, "valid": 2, "skipped": 0}
        assert [v["assigned_ids"] for v in preview["valid"]] == [
            [],
            [str(admin_profile.id)],
        ]
        assert preview["dropped"] == [{"field": "assigned_emails", "count": 1}]

        response = _post(admin_client, COMMIT, data)
        assert response.status_code == 200, response.json()
        assert not Lead.objects.get(first_name="Ada").assigned_to.exists()
        assert list(Lead.objects.get(first_name="Grace").assigned_to.all()) == [
            admin_profile
        ]

    def test_unreadable_email_dropped_and_not_a_duplicate(
        self, admin_client, admin_profile
    ):
        data = _csv([["Name", "Email"], ["Ada Byte", "n/a"], ["Grace Hopper", "N/A"]])
        body = _post(admin_client, PREVIEW, data).json()
        assert body["summary"] == {"total": 2, "valid": 2, "skipped": 0}
        assert body["dropped"] == [{"field": "email", "count": 2}]


@pytest.mark.django_db
class TestRefusals:
    @pytest.mark.parametrize("url", BOTH)
    def test_required_custom_field_still_refuses_file(
        self, admin_client, admin_profile, org_a, url
    ):
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Lead",
            key="region",
            label="Region",
            field_type="text",
            is_required=True,
            is_active=True,
        )
        data = _csv(
            [["first_name", "last_name", "email"], ["Ada", "Byte", "ada@x.com"]]
        )
        legacy = admin_client.post(
            PREVIEW, {"file": _upload("leads.csv", data)}, format="multipart"
        ).json()
        assert "region" in legacy["header_error"]

        response = _post(admin_client, url, data)
        assert response.status_code == 400
        assert response.json() == {"error": True, "message": legacy["header_error"]}
        assert not Lead.objects.exists()

    @pytest.mark.parametrize("url", BOTH)
    @pytest.mark.parametrize("target", ["org", "created_by", "id", "is_active"])
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
        assert not Lead.objects.exists()

    @pytest.mark.parametrize("url", BOTH)
    def test_xls_refused_400(self, admin_client, admin_profile, url):
        response = _post(
            admin_client, url, b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", name="leads.xls"
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
        assert not Lead.objects.exists()

    def test_mapped_import_stays_in_own_org(
        self, admin_client, admin_profile, admin_user, org_a, org_b, org_b_client
    ):
        data = _csv([["Name", "Email"], ["Ada Lovelace", "ada@x.com"]])
        response = _post(admin_client, COMMIT, data)
        assert response.status_code == 200, response.json()
        lead = Lead.objects.get(org=org_a)
        assert lead.created_by_id == admin_user.id
        with rls_org(org_b):
            assert Lead.objects.filter(org=org_b).count() == 0

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

        monkeypatch.setattr("leads.csv_import._commit_validated", _race)
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
            PREVIEW, {"file": _upload("leads.csv", data)}, format="multipart"
        )
        assert response.status_code == 200, response.json()
        body = response.json()
        assert "header_error" in body and "errors" in body
        assert "columns" not in body
        assert body["summary"] == {"total": 1, "valid": 1, "invalid": 0}


class TestTables:
    def test_fields_are_the_template_plus_full_name(self):
        names = [name for name, _label, _required in LEAD_FIELDS]
        assert names == [*KNOWN_HEADERS, "full_name"]
        assert not [name for name, _label, required in LEAD_FIELDS if required]

    def test_template_headers_guess_themselves(self):
        assert guess_mapping(list(KNOWN_HEADERS), LEAD_SYNONYMS) == list(KNOWN_HEADERS)

    def test_every_synonym_target_is_importable(self):
        names = {name for name, _label, _required in LEAD_FIELDS}
        assert set(LEAD_SYNONYMS) <= names
