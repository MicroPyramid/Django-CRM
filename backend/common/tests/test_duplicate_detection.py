"""
Tests for common/duplicate_detection.py - DuplicateDetector utility class.

Covers normalize_phone, normalize_domain, find_duplicate_contacts,
find_duplicate_leads, and find_duplicate_accounts.

Run with: pytest common/tests/test_duplicate_detection.py -v
"""

import pytest

from accounts.models import Account
from common.duplicate_detection import DuplicateDetector
from contacts.models import Contact
from leads.models import Lead


class TestNormalizePhone:
    """Tests for DuplicateDetector.normalize_phone static method."""

    def test_empty_string(self):
        assert DuplicateDetector.normalize_phone("") == ""

    def test_none(self):
        assert DuplicateDetector.normalize_phone(None) == ""

    def test_digits_only(self):
        assert DuplicateDetector.normalize_phone("1234567890") == "1234567890"

    def test_strips_non_digits(self):
        assert DuplicateDetector.normalize_phone("+1 (555) 123-4567") == "5551234567"

    def test_returns_last_10_digits_for_long_numbers(self):
        # Country code + 10-digit number: only last 10 returned
        assert DuplicateDetector.normalize_phone("15551234567") == "5551234567"

    def test_short_number_returned_as_is(self):
        assert DuplicateDetector.normalize_phone("12345") == "12345"

    def test_exactly_10_digits(self):
        assert DuplicateDetector.normalize_phone("5551234567") == "5551234567"

    def test_strips_dashes_and_spaces(self):
        assert DuplicateDetector.normalize_phone("555-123-4567") == "5551234567"


class TestNormalizeDomain:
    """Tests for DuplicateDetector.normalize_domain static method."""

    def test_empty_string(self):
        assert DuplicateDetector.normalize_domain("") == ""

    def test_none(self):
        assert DuplicateDetector.normalize_domain(None) == ""

    def test_https_url(self):
        assert DuplicateDetector.normalize_domain("https://example.com") == "example.com"

    def test_http_url(self):
        assert DuplicateDetector.normalize_domain("http://example.com") == "example.com"

    def test_www_prefix_removed(self):
        assert DuplicateDetector.normalize_domain("https://www.example.com") == "example.com"

    def test_path_removed(self):
        assert DuplicateDetector.normalize_domain("https://example.com/path/page") == "example.com"

    def test_lowercase(self):
        assert DuplicateDetector.normalize_domain("HTTPS://EXAMPLE.COM") == "example.com"

    def test_bare_domain(self):
        assert DuplicateDetector.normalize_domain("example.com") == "example.com"


@pytest.mark.django_db
class TestFindDuplicateContacts:
    """Tests for DuplicateDetector.find_duplicate_contacts."""

    def test_no_duplicates(self, org_a):
        Contact.objects.create(
            first_name="Alice", last_name="Smith", email="alice@example.com", org=org_a
        )
        dupes = DuplicateDetector.find_duplicate_contacts(
            org_a, email="bob@example.com"
        )
        assert len(dupes) == 0

    def test_email_match(self, org_a):
        c = Contact.objects.create(
            first_name="Alice", last_name="Smith", email="alice@example.com", org=org_a
        )
        dupes = DuplicateDetector.find_duplicate_contacts(
            org_a, email="Alice@Example.com"
        )
        assert c in dupes

    def test_phone_match(self, org_a):
        c = Contact.objects.create(
            first_name="Alice",
            last_name="Smith",
            phone="555-123-4567",
            org=org_a,
        )
        dupes = DuplicateDetector.find_duplicate_contacts(
            org_a, phone="+1 (555) 123-4567"
        )
        assert c in dupes

    def test_phone_too_short_skipped(self, org_a):
        Contact.objects.create(
            first_name="Alice", last_name="Smith", phone="12345", org=org_a
        )
        dupes = DuplicateDetector.find_duplicate_contacts(
            org_a, phone="12345"
        )
        assert len(dupes) == 0

    def test_name_match(self, org_a):
        c = Contact.objects.create(
            first_name="Alice", last_name="Smith", org=org_a
        )
        dupes = DuplicateDetector.find_duplicate_contacts(
            org_a, first_name="alice", last_name="smith"
        )
        assert c in dupes

    def test_exclude_id(self, org_a):
        c = Contact.objects.create(
            first_name="Alice", last_name="Smith", email="alice@example.com", org=org_a
        )
        dupes = DuplicateDetector.find_duplicate_contacts(
            org_a, email="alice@example.com", exclude_id=c.pk
        )
        assert len(dupes) == 0

    def test_no_duplicate_entries(self, org_a):
        """A single contact matching by email and name should appear only once."""
        c = Contact.objects.create(
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            org=org_a,
        )
        dupes = DuplicateDetector.find_duplicate_contacts(
            org_a,
            email="alice@example.com",
            first_name="Alice",
            last_name="Smith",
        )
        assert dupes.count(c) == 1

    def test_inactive_contacts_excluded(self, org_a):
        Contact.objects.create(
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            org=org_a,
            is_active=False,
        )
        dupes = DuplicateDetector.find_duplicate_contacts(
            org_a, email="alice@example.com"
        )
        assert len(dupes) == 0

    def test_cross_org_isolation(self, org_a, org_b):
        Contact.objects.create(
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            org=org_b,
        )
        dupes = DuplicateDetector.find_duplicate_contacts(
            org_a, email="alice@example.com"
        )
        assert len(dupes) == 0

    def test_partial_name_no_match(self, org_a):
        """Providing only first_name (no last_name) should not trigger name matching."""
        Contact.objects.create(
            first_name="Alice", last_name="Smith", org=org_a
        )
        dupes = DuplicateDetector.find_duplicate_contacts(
            org_a, first_name="Alice"
        )
        assert len(dupes) == 0


@pytest.mark.django_db
class TestFindDuplicateLeads:
    """Tests for DuplicateDetector.find_duplicate_leads."""

    def test_email_match(self, org_a):
        lead = Lead.objects.create(
            first_name="Bob",
            last_name="Jones",
            email="bob@example.com",
            org=org_a,
        )
        dupes = DuplicateDetector.find_duplicate_leads(
            org_a, email="BOB@EXAMPLE.COM"
        )
        assert lead in dupes

    def test_phone_match(self, org_a):
        lead = Lead.objects.create(
            first_name="Bob",
            last_name="Jones",
            phone="555-987-6543",
            org=org_a,
        )
        dupes = DuplicateDetector.find_duplicate_leads(
            org_a, phone="(555) 987-6543"
        )
        assert lead in dupes

    def test_name_match(self, org_a):
        lead = Lead.objects.create(
            first_name="Bob", last_name="Jones", org=org_a
        )
        dupes = DuplicateDetector.find_duplicate_leads(
            org_a, first_name="bob", last_name="jones"
        )
        assert lead in dupes

    def test_company_name_match(self, org_a):
        lead = Lead.objects.create(
            first_name="Bob",
            last_name="Jones",
            company_name="Acme Corporation",
            org=org_a,
        )
        dupes = DuplicateDetector.find_duplicate_leads(
            org_a, company_name="Acme"
        )
        assert lead in dupes

    def test_company_name_too_short(self, org_a):
        Lead.objects.create(
            first_name="Bob",
            last_name="Jones",
            company_name="AB Corp",
            org=org_a,
        )
        dupes = DuplicateDetector.find_duplicate_leads(
            org_a, company_name="AB"
        )
        assert len(dupes) == 0

    def test_exclude_id(self, org_a):
        lead = Lead.objects.create(
            first_name="Bob",
            last_name="Jones",
            email="bob@example.com",
            org=org_a,
        )
        dupes = DuplicateDetector.find_duplicate_leads(
            org_a, email="bob@example.com", exclude_id=lead.pk
        )
        assert len(dupes) == 0

    def test_no_duplicate_entries(self, org_a):
        """Same lead matching by email and name should appear only once."""
        lead = Lead.objects.create(
            first_name="Bob",
            last_name="Jones",
            email="bob@example.com",
            org=org_a,
        )
        dupes = DuplicateDetector.find_duplicate_leads(
            org_a,
            email="bob@example.com",
            first_name="Bob",
            last_name="Jones",
        )
        assert dupes.count(lead) == 1

    def test_inactive_leads_excluded(self, org_a):
        Lead.objects.create(
            first_name="Bob",
            last_name="Jones",
            email="bob@example.com",
            org=org_a,
            is_active=False,
        )
        dupes = DuplicateDetector.find_duplicate_leads(
            org_a, email="bob@example.com"
        )
        assert len(dupes) == 0


@pytest.mark.django_db
class TestFindDuplicateAccounts:
    """Tests for DuplicateDetector.find_duplicate_accounts."""

    def test_exact_name_match(self, org_a):
        acct = Account.objects.create(name="Acme Corp", org=org_a)
        dupes = DuplicateDetector.find_duplicate_accounts(
            org_a, name="acme corp"
        )
        assert acct in dupes

    def test_partial_name_match(self, org_a):
        acct = Account.objects.create(name="Acme Industries", org=org_a)
        dupes = DuplicateDetector.find_duplicate_accounts(
            org_a, name="Acme Corp"
        )
        # "Acme Industries" starts with "Acme" so it's a partial match
        assert acct in dupes

    def test_email_match(self, org_a):
        acct = Account.objects.create(
            name="Acme Corp", email="info@acme.com", org=org_a
        )
        dupes = DuplicateDetector.find_duplicate_accounts(
            org_a, email="INFO@ACME.COM"
        )
        assert acct in dupes

    def test_website_match(self, org_a):
        acct = Account.objects.create(
            name="Acme Corp",
            website="https://www.acme.com/about",
            org=org_a,
        )
        dupes = DuplicateDetector.find_duplicate_accounts(
            org_a, website="http://acme.com"
        )
        assert acct in dupes

    def test_phone_match(self, org_a):
        acct = Account.objects.create(
            name="Acme Corp", phone="555-111-2222", org=org_a
        )
        dupes = DuplicateDetector.find_duplicate_accounts(
            org_a, phone="(555) 111-2222"
        )
        assert acct in dupes

    def test_exclude_id(self, org_a):
        acct = Account.objects.create(
            name="Acme Corp", email="info@acme.com", org=org_a
        )
        dupes = DuplicateDetector.find_duplicate_accounts(
            org_a, email="info@acme.com", exclude_id=acct.pk
        )
        assert len(dupes) == 0

    def test_no_duplicate_entries_across_matchers(self, org_a):
        """Account matching by name and email should appear only once."""
        acct = Account.objects.create(
            name="Acme Corp", email="info@acme.com", org=org_a
        )
        dupes = DuplicateDetector.find_duplicate_accounts(
            org_a, name="Acme Corp", email="info@acme.com"
        )
        assert dupes.count(acct) == 1

    def test_cross_org_isolation(self, org_a, org_b):
        Account.objects.create(name="Acme Corp", org=org_b)
        dupes = DuplicateDetector.find_duplicate_accounts(
            org_a, name="Acme Corp"
        )
        assert len(dupes) == 0

    def test_no_args_returns_empty(self, org_a):
        Account.objects.create(name="Acme Corp", org=org_a)
        dupes = DuplicateDetector.find_duplicate_accounts(org_a)
        assert len(dupes) == 0

    def test_short_first_word_no_partial_match(self, org_a):
        """First word less than 3 chars should not trigger partial matching."""
        Account.objects.create(name="AB Industries", org=org_a)
        dupes = DuplicateDetector.find_duplicate_accounts(
            org_a, name="AB Corp"
        )
        # Exact match won't find "AB Industries", and first word "AB" is < 3 chars
        assert len(dupes) == 0
