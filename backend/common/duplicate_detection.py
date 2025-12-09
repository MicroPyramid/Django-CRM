"""
Duplicate detection service for CRM entities.

Provides methods to find potential duplicate records based on
email, phone, name, and other identifying fields.
"""

import re
from typing import TYPE_CHECKING

from django.db.models import Q

if TYPE_CHECKING:
    from accounts.models import Account
    from contacts.models import Contact
    from leads.models import Lead


class DuplicateDetector:
    """Service for detecting potential duplicate records."""

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        Normalize a phone number by removing all non-digit characters.
        Returns the last 10 digits for comparison purposes.
        """
        if not phone:
            return ""
        digits_only = re.sub(r"[^\d]", "", phone)
        return digits_only[-10:] if len(digits_only) >= 10 else digits_only

    @staticmethod
    def normalize_domain(website: str) -> str:
        """Extract and normalize domain from a website URL."""
        if not website:
            return ""
        domain = website.lower()
        domain = domain.replace("https://", "").replace("http://", "")
        domain = domain.replace("www.", "")
        domain = domain.split("/")[0]  # Remove path
        return domain

    @classmethod
    def find_duplicate_contacts(
        cls,
        org,
        email: str | None = None,
        phone: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        exclude_id=None,
    ) -> list["Contact"]:
        """
        Find potential duplicate contacts based on email, phone, or name.

        Args:
            org: The organization to search within
            email: Email address to match
            phone: Phone number to match (normalized)
            first_name: First name for fuzzy matching
            last_name: Last name for fuzzy matching
            exclude_id: ID to exclude from results (for updates)

        Returns:
            List of potential duplicate Contact objects
        """
        from contacts.models import Contact

        duplicates = []
        base_qs = Contact.objects.filter(org=org, is_active=True)

        if exclude_id:
            base_qs = base_qs.exclude(pk=exclude_id)

        # Exact email match (case-insensitive)
        if email:
            email_matches = base_qs.filter(email__iexact=email)
            duplicates.extend(list(email_matches))

        # Normalized phone match
        if phone:
            normalized = cls.normalize_phone(phone)
            if len(normalized) >= 7:
                # Get all contacts with phones and filter in Python
                phone_candidates = base_qs.exclude(phone__isnull=True).exclude(phone="")
                for contact in phone_candidates:
                    if cls.normalize_phone(contact.phone) == normalized:
                        if contact not in duplicates:
                            duplicates.append(contact)

        # Name match (first + last name combination)
        if first_name and last_name:
            name_matches = base_qs.filter(
                first_name__iexact=first_name, last_name__iexact=last_name
            )
            for contact in name_matches:
                if contact not in duplicates:
                    duplicates.append(contact)

        return duplicates

    @classmethod
    def find_duplicate_leads(
        cls,
        org,
        email: str | None = None,
        phone: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        company_name: str | None = None,
        exclude_id=None,
    ) -> list["Lead"]:
        """
        Find potential duplicate leads based on email, phone, name, or company.

        Args:
            org: The organization to search within
            email: Email address to match
            phone: Phone number to match (normalized)
            first_name: First name for fuzzy matching
            last_name: Last name for fuzzy matching
            company_name: Company name for fuzzy matching
            exclude_id: ID to exclude from results (for updates)

        Returns:
            List of potential duplicate Lead objects
        """
        from leads.models import Lead

        duplicates = []
        base_qs = Lead.objects.filter(org=org, is_active=True)

        if exclude_id:
            base_qs = base_qs.exclude(pk=exclude_id)

        # Exact email match (case-insensitive)
        if email:
            email_matches = base_qs.filter(email__iexact=email)
            duplicates.extend(list(email_matches))

        # Normalized phone match
        if phone:
            normalized = cls.normalize_phone(phone)
            if len(normalized) >= 7:
                phone_candidates = base_qs.exclude(phone__isnull=True).exclude(phone="")
                for lead in phone_candidates:
                    if cls.normalize_phone(lead.phone) == normalized:
                        if lead not in duplicates:
                            duplicates.append(lead)

        # Name match
        if first_name and last_name:
            name_matches = base_qs.filter(
                first_name__iexact=first_name, last_name__iexact=last_name
            )
            for lead in name_matches:
                if lead not in duplicates:
                    duplicates.append(lead)

        # Company name match (fuzzy - contains)
        if company_name and len(company_name) >= 3:
            company_matches = base_qs.filter(company_name__icontains=company_name)
            for lead in company_matches:
                if lead not in duplicates:
                    duplicates.append(lead)

        return duplicates

    @classmethod
    def find_duplicate_accounts(
        cls,
        org,
        name: str | None = None,
        email: str | None = None,
        website: str | None = None,
        phone: str | None = None,
        exclude_id=None,
    ) -> list["Account"]:
        """
        Find potential duplicate accounts based on name, email, website, or phone.

        Args:
            org: The organization to search within
            name: Account name to match (fuzzy)
            email: Email address to match
            website: Website URL to match (domain normalized)
            phone: Phone number to match (normalized)
            exclude_id: ID to exclude from results (for updates)

        Returns:
            List of potential duplicate Account objects
        """
        from accounts.models import Account

        duplicates = []
        base_qs = Account.objects.filter(org=org, is_active=True)

        if exclude_id:
            base_qs = base_qs.exclude(pk=exclude_id)

        # Exact name match (case-insensitive)
        if name:
            name_matches = base_qs.filter(name__iexact=name)
            duplicates.extend(list(name_matches))

            # Also check for partial matches on first word (for company variations)
            first_word = name.split()[0] if name else ""
            if len(first_word) >= 3:
                partial_matches = base_qs.filter(name__istartswith=first_word).exclude(
                    name__iexact=name
                )
                for account in partial_matches:
                    if account not in duplicates:
                        duplicates.append(account)

        # Exact email match
        if email:
            email_matches = base_qs.filter(email__iexact=email)
            for account in email_matches:
                if account not in duplicates:
                    duplicates.append(account)

        # Website domain match
        if website:
            domain = cls.normalize_domain(website)
            if domain:
                website_candidates = base_qs.exclude(website__isnull=True).exclude(
                    website=""
                )
                for account in website_candidates:
                    if cls.normalize_domain(account.website) == domain:
                        if account not in duplicates:
                            duplicates.append(account)

        # Normalized phone match
        if phone:
            normalized = cls.normalize_phone(phone)
            if len(normalized) >= 7:
                phone_candidates = base_qs.exclude(phone__isnull=True).exclude(phone="")
                for account in phone_candidates:
                    if cls.normalize_phone(account.phone) == normalized:
                        if account not in duplicates:
                            duplicates.append(account)

        return duplicates
