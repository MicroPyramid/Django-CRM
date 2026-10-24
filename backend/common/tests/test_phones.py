"""`common.phones.to_e164`: one form for a phone number, whatever was typed."""

import pytest

from common.phones import to_e164


def test_an_international_number_and_its_local_form_agree():
    assert (
        to_e164("+1 (555) 123-4567", None)
        == to_e164("555-123-4567", "US")
        == "+15551234567"
    )


def test_a_trunk_zero_is_dropped():
    assert to_e164("020 7946 0958", "GB") == "+442079460958"


def test_the_region_is_case_insensitive():
    assert to_e164("555-123-4567", "us") == "+15551234567"


def test_an_international_number_ignores_the_region():
    assert to_e164("+44 20 7946 0958", "US") == "+442079460958"
    assert to_e164("+91 98765 43210", "US") == "+919876543210"


def test_a_number_dialable_only_locally_is_empty():
    # Seven digits with no area code: phonenumbers calls it possible "locally".
    assert to_e164("123-4567", "US") == ""


def test_a_non_string_region_never_raises():
    assert to_e164("555", 1) == ""
    assert to_e164("+1 555 123 4567", 1) == "+15551234567"


@pytest.mark.parametrize(
    "raw, region",
    [
        ("12", "US"),
        (None, "US"),
        ("", "US"),
        ("   ", "US"),
        ("abc", None),
        # A local number means nothing without a country.
        ("555-123-4567", None),
        ("555-123-4567", ""),
        # Not a region phonenumbers knows.
        ("555-123-4567", "ZZ"),
        ("1" * 300, "US"),
        ("+" + "9" * 40, None),
    ],
)
def test_what_cannot_be_a_number_is_empty(raw, region):
    assert to_e164(raw, region) == ""


def test_a_non_string_never_raises():
    assert to_e164(5551234567, "US") == "+15551234567"
