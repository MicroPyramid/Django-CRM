"""An org chooses how its invoice and estimate numbers look (#802).

A number is the org's prefix, then the date (if the org dates its numbers) and
a hyphen, then a zero-padded counter. The defaults reproduce the format every
org had before the setting existed, `INV-YYYYMMDD-0001`, so nobody's numbering
changes until an admin changes it. A number already issued never moves.

The settings live on `Org` and are written only through `PATCH
/api/org/settings/`, which only an admin may call.
"""

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status

from conftest import rls_org
from invoices.models import Estimate, Invoice

URL = "/api/org/settings/"


def _number(org, **fields):
    return Invoice.objects.create(
        invoice_title="Numbered", client_email="c@example.com", org=org, **fields
    ).invoice_number


def _estimate_number(org):
    return Estimate.objects.create(title="Numbered", org=org).estimate_number


def _numbering(org, **settings):
    for name, value in settings.items():
        setattr(org, name, value)
    org.save()


class TestFormat:
    def test_the_defaults_are_the_format_every_org_already_had(self, org_a):
        assert (org_a.invoice_number_prefix, org_a.estimate_number_prefix) == (
            "INV-",
            "EST-",
        )
        assert (org_a.number_date_part, org_a.number_padding) == ("DAY", 4)
        assert org_a.invoice_number_start == 1
        day = f"{timezone.localdate():%Y%m%d}"
        assert _number(org_a) == f"INV-{day}-0001"
        assert _estimate_number(org_a) == f"EST-{day}-0001"

    def test_no_date_is_one_running_sequence(self, org_a):
        _numbering(org_a, number_date_part="NONE")
        assert [_number(org_a), _number(org_a)] == ["INV-0001", "INV-0002"]

    def test_a_prefix_needs_no_separator(self, org_a):
        _numbering(org_a, invoice_number_prefix="INV", number_date_part="NONE")
        assert _number(org_a) == "INV0001"

    def test_company_initials_in_the_prefix(self, org_a):
        _numbering(org_a, invoice_number_prefix="INVNSD-", number_date_part="NONE")
        assert _number(org_a) == "INVNSD-0001"

    @pytest.mark.parametrize(
        "date_part,date_format", [("YEAR", "%Y"), ("MONTH", "%Y%m")]
    )
    def test_a_dated_number_carries_the_period(self, org_a, date_part, date_format):
        _numbering(org_a, number_date_part=date_part)
        period = f"{timezone.localdate():{date_format}}"
        assert [_number(org_a), _number(org_a)] == [
            f"INV-{period}-0001",
            f"INV-{period}-0002",
        ]

    def test_a_dated_counter_restarts_in_a_new_period(self, org_a):
        """Last year's numbers are another series, so this year starts at 1."""
        _numbering(org_a, number_date_part="YEAR")
        last_year = timezone.localdate().year - 1
        _number(org_a, invoice_number=f"INV-{last_year}-0417")
        assert _number(org_a) == f"INV-{timezone.localdate():%Y}-0001"

    def test_padding_sets_the_counter_width(self, org_a):
        _numbering(org_a, number_date_part="NONE", number_padding=6)
        assert _number(org_a) == "INV-000001"

    def test_a_counter_wider_than_the_padding_is_not_cut(self, org_a):
        _numbering(org_a, number_date_part="NONE", number_padding=2)
        _number(org_a, invoice_number="INV-99")
        assert _number(org_a) == "INV-100"

    def test_changing_the_padding_carries_the_count_on(self, org_a):
        _numbering(org_a, number_date_part="NONE")
        _number(org_a, invoice_number="INV-0041")
        _numbering(org_a, number_padding=6)
        assert _number(org_a) == "INV-000042"

    def test_estimates_take_their_own_prefix_and_share_the_rest(self, org_a):
        _numbering(
            org_a,
            invoice_number_prefix="INVNSD-",
            estimate_number_prefix="ESTNSD-",
            number_date_part="YEAR",
            number_padding=5,
        )
        year = f"{timezone.localdate():%Y}"
        assert _number(org_a) == f"INVNSD-{year}-00001"
        assert _estimate_number(org_a) == f"ESTNSD-{year}-00001"

    def test_each_org_numbers_in_its_own_format(self, org_a, org_b):
        _numbering(org_a, invoice_number_prefix="A-", number_date_part="NONE")
        with rls_org(org_b):
            _numbering(org_b, invoice_number_prefix="B", number_date_part="NONE")
            assert _number(org_b) == "B0001"
        assert _number(org_a) == "A-0001"


class TestEarlierNumbers:
    """Numbers issued under an earlier format stay where they are, and must
    neither be read as this format's counter nor stop the next save."""

    def test_dropping_the_date_starts_a_new_sequence(self, org_a):
        """`INV-20260915-0001` starts with `INV-`, but what follows is not a
        counter. Read as one, it either became 20260916 or failed the cast,
        and every invoice save in the org failed with it."""
        _number(org_a)
        _number(org_a, invoice_number="INV-20260915-0007")
        _numbering(org_a, number_date_part="NONE")
        assert _number(org_a) == "INV-0001"

    def test_a_long_run_of_digits_does_not_overflow_the_count(self, org_a):
        """More digits than a 32-bit integer holds, from an old prefix that
        ended in digits. An integer cast fails on it in PostgreSQL."""
        _numbering(org_a, number_date_part="NONE")
        _number(org_a, invoice_number="INV-123456789012345")
        assert _number(org_a) == "INV-123456789012346"


class TestStartingNumber:
    def test_an_undated_sequence_starts_where_the_org_left_off(self, org_a):
        _numbering(org_a, number_date_part="NONE", invoice_number_start=1042)
        assert [_number(org_a), _number(org_a)] == ["INV-1042", "INV-1043"]

    def test_numbers_already_past_the_start_carry_on(self, org_a):
        _numbering(org_a, number_date_part="NONE")
        _number(org_a, invoice_number="INV-0050")
        _numbering(org_a, invoice_number_start=10)
        assert _number(org_a) == "INV-0051"

    def test_estimates_do_not_take_the_invoice_start(self, org_a):
        _numbering(org_a, number_date_part="NONE", invoice_number_start=1042)
        assert _estimate_number(org_a) == "EST-0001"

    def test_a_dated_sequence_cannot_be_stored_with_a_start(self, org_a):
        """A dated counter restarts each period, and a floor would restart it
        at the floor. The serializer refuses this in words; the constraint
        stops any other write path storing it."""
        org_a.number_date_part = "YEAR"
        org_a.invoice_number_start = 1042
        with pytest.raises(IntegrityError), transaction.atomic():
            org_a.save()


class TestSettingsAPI:
    def test_any_member_reads_the_numbering(self, user_client, org_a):
        response = user_client.get(URL)
        assert response.status_code == status.HTTP_200_OK
        assert {
            name: response.data[name]
            for name in (
                "invoice_number_prefix",
                "estimate_number_prefix",
                "number_date_part",
                "number_padding",
                "invoice_number_start",
            )
        } == {
            "invoice_number_prefix": "INV-",
            "estimate_number_prefix": "EST-",
            "number_date_part": "DAY",
            "number_padding": 4,
            "invoice_number_start": 1,
        }

    def test_an_admin_sets_the_numbering(self, admin_client, org_a):
        response = admin_client.patch(
            URL,
            {
                "invoice_number_prefix": "INVNSD-",
                "estimate_number_prefix": "ESTNSD-",
                "number_date_part": "NONE",
                "number_padding": 5,
                "invoice_number_start": 1042,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        org_a.refresh_from_db()
        assert _number(org_a) == "INVNSD-01042"
        assert _estimate_number(org_a) == "ESTNSD-00001"

    def test_a_member_cannot_change_the_numbering(self, user_client, org_a):
        response = user_client.patch(
            URL,
            {"invoice_number_prefix": "X-", "number_date_part": "NONE"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        org_a.refresh_from_db()
        assert (org_a.invoice_number_prefix, org_a.number_date_part) == (
            "INV-",
            "DAY",
        )

    @pytest.mark.parametrize("prefix", ["", "INV", "INVNSD-", "A_1", "X" * 20])
    def test_a_plain_prefix_is_accepted(self, admin_client, org_a, prefix):
        response = admin_client.patch(
            URL, {"invoice_number_prefix": prefix}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        org_a.refresh_from_db()
        assert org_a.invoice_number_prefix == prefix

    @pytest.mark.parametrize(
        "field,prefix",
        [
            # The number is the PDF's filename in a Content-Disposition header.
            ("invoice_number_prefix", 'INV"; x='),
            ("invoice_number_prefix", "INV/2026/"),
            ("invoice_number_prefix", "INV\r\nX-Injected: 1"),
            ("invoice_number_prefix", "INV 1"),
            ("invoice_number_prefix", "FACTÜRA-"),
            ("estimate_number_prefix", "EST/"),
            ("invoice_number_prefix", "X" * 21),
        ],
    )
    def test_a_prefix_outside_the_allowed_characters_is_refused(
        self, admin_client, org_a, field, prefix
    ):
        response = admin_client.patch(URL, {field: prefix}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field in response.data
        org_a.refresh_from_db()
        assert getattr(org_a, field) in ("INV-", "EST-")

    @pytest.mark.parametrize(
        "field,value",
        [
            ("number_padding", 0),
            ("number_padding", 11),
            ("number_date_part", "WEEK"),
            ("invoice_number_start", 0),
            ("invoice_number_start", 1_000_000_000),
        ],
    )
    def test_out_of_range_values_are_refused(self, admin_client, org_a, field, value):
        body = {field: value, "number_date_part": "NONE"}
        if field == "number_date_part":
            body = {field: value}
        response = admin_client.patch(URL, body, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field in response.data

    def test_a_start_with_a_dated_number_is_refused_in_words(self, admin_client, org_a):
        response = admin_client.patch(
            URL,
            {"number_date_part": "YEAR", "invoice_number_start": 1042},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "restarts at 1" in str(response.data["invoice_number_start"])

    def test_adding_a_date_to_a_started_sequence_must_reset_the_start(
        self, admin_client, org_a
    ):
        _numbering(org_a, number_date_part="NONE", invoice_number_start=1042)

        kept = admin_client.patch(URL, {"number_date_part": "YEAR"}, format="json")
        assert kept.status_code == status.HTTP_400_BAD_REQUEST
        assert "invoice_number_start" in kept.data

        reset = admin_client.patch(
            URL,
            {"number_date_part": "YEAR", "invoice_number_start": 1},
            format="json",
        )
        assert reset.status_code == status.HTTP_200_OK, reset.data
        org_a.refresh_from_db()
        assert (org_a.number_date_part, org_a.invoice_number_start) == ("YEAR", 1)
