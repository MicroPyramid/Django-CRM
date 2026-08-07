"""Org-scoped global search behind ``GET /api/search/?q=``, the ⌘K palette.

ONE endpoint, deliberately. The org comes from the JWT (`request.profile.org`)
exactly once and every queryset is filtered by it; a per-model fan-out from the
browser would be as many chances to read another tenant's rows.

Each type also honours the SAME read visibility as its own list view, so search
can never surface a record the caller could not open from the list:

* leads / opportunities / invoices, admin (role ``ADMIN`` or a Django
  superuser) sees the whole org; everyone else sees only what they created or
  were assigned.
* accounts / contacts, admin (role ``ADMIN`` or the org-admin flag) sees the
  whole org; everyone else sees created-or-assigned.
* tickets. Reuse ``visible_cases_qs`` (adds the watcher clause).
* knowledge-base articles. Org-wide, every member reads them.

Matching stays on the server; the whole record set never reaches the browser.
"""

from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Account
from cases.access import is_org_admin, visible_cases_qs
from cases.models import Solution
from common.permissions import HasOrgContext
from contacts.models import Contact
from invoices.models import Invoice
from leads.models import Lead
from opportunity.models import Opportunity

# Rows per type. Small on purpose. The palette shows a handful per group and
# the point is the fastest match, not an exhaustive report.
PER_TYPE = 6
# One-character queries match almost everything; wait for a second character.
MIN_QUERY = 2


def _own_filter(profile):
    """The created-or-assigned clause every assignable list view uses.

    ``created_by`` is a FK to ``User`` (not Profile), so it is compared against
    ``profile.user``: comparing it to the Profile is the silent always-False
    bug this codebase has hit before.
    """
    return Q(created_by=profile.user) | Q(assigned_to=profile)


def _scope_orgadmin(qs, profile):
    """accounts / contacts rule: admin = role ADMIN or the org-admin flag."""
    if is_org_admin(profile):
        return qs
    return qs.filter(_own_filter(profile)).distinct()


def _scope_superuser(qs, profile, user):
    """leads / opportunities / invoices rule: admin = role ADMIN or superuser."""
    if is_org_admin(profile) or user.is_superuser:
        return qs
    return qs.filter(_own_filter(profile)).distinct()


class GlobalSearchView(APIView):
    """``GET /api/search/?q=<query>``. A handful of matches per record type."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        if len(q) < MIN_QUERY:
            return Response({"query": q, "results": []})

        profile = request.profile
        org = profile.org
        user = request.user
        results = []

        # Leads
        leads = _scope_superuser(Lead.objects.filter(org=org), profile, user).filter(
            Q(title__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
            | Q(company_name__icontains=q)
        )[:PER_TYPE]
        for lead in leads:
            name = lead.title or f"{lead.first_name} {lead.last_name}".strip()
            results.append(
                {
                    "type": "lead",
                    "id": str(lead.id),
                    "title": name or lead.email or "Untitled lead",
                    "subtitle": lead.company_name or lead.email or "",
                }
            )

        # Deals (Opportunity)
        deals = _scope_superuser(
            Opportunity.objects.filter(org=org).select_related("account"),
            profile,
            user,
        ).filter(
            Q(name__icontains=q)
            | Q(description__icontains=q)
            | Q(account__name__icontains=q)
        )[:PER_TYPE]
        for deal in deals:
            results.append(
                {
                    "type": "deal",
                    "id": str(deal.id),
                    "title": deal.name,
                    "subtitle": (deal.account.name if deal.account_id else "")
                    or deal.stage
                    or "",
                }
            )

        # Accounts
        accounts = _scope_orgadmin(Account.objects.filter(org=org), profile).filter(
            Q(name__icontains=q)
            | Q(email__icontains=q)
            | Q(website__icontains=q)
            | Q(industry__icontains=q)
        )[:PER_TYPE]
        for account in accounts:
            results.append(
                {
                    "type": "account",
                    "id": str(account.id),
                    "title": account.name,
                    "subtitle": account.email or account.industry or "",
                }
            )

        # Contacts
        contacts = _scope_orgadmin(Contact.objects.filter(org=org), profile).filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
            | Q(organization__icontains=q)
        )[:PER_TYPE]
        for contact in contacts:
            name = f"{contact.first_name} {contact.last_name}".strip()
            results.append(
                {
                    "type": "contact",
                    "id": str(contact.id),
                    "title": name or contact.email or "Unnamed contact",
                    "subtitle": contact.organization or contact.email or "",
                }
            )

        # Tickets (Case): the module's own read-visibility helper
        cases = (
            visible_cases_qs(profile)
            .select_related("account")
            .filter(
                Q(name__icontains=q)
                | Q(description__icontains=q)
                | Q(account__name__icontains=q)
            )[:PER_TYPE]
        )
        for case in cases:
            results.append(
                {
                    "type": "ticket",
                    "id": str(case.id),
                    "title": case.name,
                    "subtitle": (case.account.name if case.account_id else "")
                    or case.status
                    or "",
                }
            )

        # Invoices
        invoices = _scope_superuser(
            Invoice.objects.filter(org=org).select_related("account"),
            profile,
            user,
        ).filter(
            Q(invoice_number__icontains=q)
            | Q(invoice_title__icontains=q)
            | Q(client_name__icontains=q)
            | Q(account__name__icontains=q)
        )[:PER_TYPE]
        for invoice in invoices:
            results.append(
                {
                    "type": "invoice",
                    "id": str(invoice.id),
                    "title": invoice.invoice_number
                    or invoice.invoice_title
                    or "Invoice",
                    "subtitle": invoice.client_name
                    or (invoice.account.name if invoice.account_id else "")
                    or invoice.status
                    or "",
                }
            )

        # Knowledge base (Solution): org-wide, every member reads
        solutions = Solution.objects.filter(org=org).filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )[:PER_TYPE]
        for solution in solutions:
            results.append(
                {
                    "type": "solution",
                    "id": str(solution.id),
                    "title": solution.title,
                    "subtitle": solution.status or "",
                }
            )

        return Response({"query": q, "results": results})
