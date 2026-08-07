"""Bulk lead import is an admin action, and its task must survive real CSVs.

``LeadUploadView`` was ``(IsAuthenticated, HasOrgContext)`` only, while the
newer contacts and cases importers both gate on ``_can_import``. Any member
could mass-create leads through it, and there was no size cap at all.

``create_lead_from_file`` carried two more defects, both of which matter more
than they look because the view dispatches it with ``.delay()``: the caller is
already holding a ``200 Leads created Successfully`` by the time any of it
runs, so a failure there is silent.

* The duplicate-title check was unscoped, so another org's titles suppressed
  rows in this one.
* ``re.match(email_regex, row.get("email"))`` sat outside the per-row ``try``.
  ``email`` is not a required CSV header (the form only requires ``title``), so
  a file without that column made ``row.get("email")`` ``None``, ``re.match``
  raise ``TypeError``, and the whole import die having created nothing.
"""

import io

import pytest
from rest_framework import status

from leads.models import Lead
from leads.tasks import create_lead_from_file

URL = "/api/leads/upload/"


def _csv(text):
    upload = io.BytesIO(text.encode())
    upload.name = "leads.csv"
    return upload


WITH_EMAIL = "title,first name,last name,email\nAcme deal,Ada,Byte,ada@example.com\n"
WITHOUT_EMAIL_COLUMN = "title,first name,last name\nAcme deal,Ada,Byte\n"


@pytest.mark.django_db
class TestUploadRequiresImportRights:
    def test_a_plain_member_is_refused(self, user_client):
        response = user_client.post(
            URL, {"leads_file": _csv(WITH_EMAIL)}, format="multipart"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_an_admin_is_allowed(self, admin_client):
        """The True direction. This is the whole feature."""
        response = admin_client.post(
            URL, {"leads_file": _csv(WITH_EMAIL)}, format="multipart"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_sales_access_is_allowed(self, user_client, user_profile):
        """Matches the contacts and cases importers, which accept this too."""
        user_profile.has_sales_access = True
        user_profile.save(update_fields=["has_sales_access"])
        response = user_client.post(
            URL, {"leads_file": _csv(WITH_EMAIL)}, format="multipart"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_an_oversized_file_is_refused(self, admin_client):
        big = "title,email\n" + "".join(
            f"Lead {n},x{n}@example.com\n" for n in range(200_000)
        )
        assert len(big.encode()) > 5 * 1024 * 1024
        response = admin_client.post(URL, {"leads_file": _csv(big)}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestImportActuallyImports:
    """The import created nothing at all, for any file, ever.

    ``lead.created_by = profile`` assigned a ``Profile`` to a FK that points at
    ``User``, so Django raised ``ValueError`` before any SQL ran, and the bare
    ``except Exception: pass`` around the row swallowed it. Every row failed the
    same way, silently, while the caller held a ``200``.
    """

    def test_a_valid_row_creates_a_lead(self, org_a, admin_profile):
        rows = [{"title": "Acme deal", "email": "ada@example.com"}]
        create_lead_from_file(rows, [], admin_profile.id, "localhost", org_a.id)
        assert Lead.objects.filter(title="Acme deal", org=org_a).count() == 1

    def test_the_importer_is_recorded_as_the_author(self, org_a, admin_profile):
        rows = [{"title": "Acme deal", "email": "ada@example.com"}]
        create_lead_from_file(rows, [], admin_profile.id, "localhost", org_a.id)
        lead = Lead.objects.get(title="Acme deal")
        assert lead.created_by_id == admin_profile.user_id


@pytest.mark.django_db
class TestImportTaskHandlesRealFiles:
    def test_a_row_with_no_email_column_does_not_kill_the_task(
        self, org_a, admin_profile
    ):
        """Previously ``TypeError``, after the caller had already been told 200."""
        rows = [{"title": "No email here", "first name": "Ada"}]
        create_lead_from_file(rows, [], admin_profile.id, "localhost", org_a.id)
        # The row is skipped for want of an email, but the task completes and
        # the rows around it are still importable.
        assert Lead.objects.filter(title="No email here").count() == 0

    def test_valid_rows_after_an_email_less_one_still_import(
        self, org_a, admin_profile
    ):
        rows = [
            {"title": "No email here", "first name": "Ada"},
            {"title": "Has email", "first name": "Bea", "email": "bea@example.com"},
        ]
        create_lead_from_file(rows, [], admin_profile.id, "localhost", org_a.id)
        assert Lead.objects.filter(title="Has email").count() == 1

    def test_another_orgs_title_does_not_suppress_the_row(
        self, org_a, org_b, admin_profile
    ):
        """The collision check was unscoped, so org B's titles blocked org A's."""
        Lead.objects.create(title="Shared title", org=org_b)
        rows = [
            {"title": "Shared title", "email": "ada@example.com"},
        ]
        create_lead_from_file(rows, [], admin_profile.id, "localhost", org_a.id)
        assert Lead.objects.filter(title="Shared title", org=org_a).count() == 1

    def test_a_title_already_in_this_org_is_still_skipped(self, org_a, admin_profile):
        """The check itself is preserved, only its scope changed."""
        Lead.objects.create(title="Existing", org=org_a)
        rows = [{"title": "Existing", "email": "ada@example.com"}]
        create_lead_from_file(rows, [], admin_profile.id, "localhost", org_a.id)
        assert Lead.objects.filter(title="Existing", org=org_a).count() == 1
