"""
Database middleware for Row-Level Security (RLS) context.

This middleware sets the PostgreSQL session variable `app.current_org`
which is used by RLS policies to filter data at the database level.

Enable RLS policies after this middleware is in place:

    ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
    CREATE POLICY org_isolation ON leads
      USING (org_id = current_setting('app.current_org', true)::uuid);

Usage in settings.py:
    MIDDLEWARE = [
        ...
        'common.middleware.get_company.GetProfileAndOrg',
        'common.middleware.rls_context.SetOrgContext',  # After GetProfileAndOrg
        ...
    ]
"""

import logging

from django.db import connection, transaction
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class SetOrgContext:
    """
    Middleware to set PostgreSQL session variable for Row-Level Security.

    This sets `app.current_org` to the user's organization ID, which is
    used by RLS policies to automatically filter data at the database level.

    Security: This provides defense-in-depth. Even if application code
    forgets to filter by org, the database will enforce isolation.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set org context before processing request
        self._set_org_context(request)

        response = self.get_response(request)

        # Reset context after request
        self._reset_org_context()

        return response

    def _set_org_context(self, request):
        """
        Set the PostgreSQL session variable for RLS.

        Args:
            request: Django request object with profile attached
        """
        if not hasattr(request, "org") or request.org is None:
            return

        org_id = str(request.org.id)

        try:
            with connection.cursor() as cursor:
                # Set the session variable (is_local=false for session scope)
                # Required because Django uses autocommit mode by default
                cursor.execute(
                    "SELECT set_config('app.current_org', %s, false)", [org_id]
                )
                logger.debug("Set RLS context: app.current_org = %s", org_id)

        except Exception as e:
            # RLS might not be configured - log but don't fail
            logger.debug("Could not set RLS context: %s", e)

    def _reset_org_context(self):
        """
        Reset the PostgreSQL session variable after request.
        Critical to prevent context leakage between requests on pooled connections.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('app.current_org', '', false)")
        except Exception:
            pass


class RequireOrgContext:
    """
    Stricter middleware that fails if org context is not set.

    Use this instead of SetOrgContext when you want to ensure
    all requests have proper org context (after RLS is fully enabled).

    Usage in settings.py:
        MIDDLEWARE = [
            ...
            'common.middleware.get_company.GetProfileAndOrg',
            'common.middleware.rls_context.RequireOrgContext',
            ...
        ]
    """

    # Paths that don't require org context
    EXEMPT_PATHS = [
        "/api/auth/refresh-token/",
        "/api/auth/me/",
        "/api/auth/switch-org/",
        "/api/auth/google/",
        "/api/auth/magic-link/request/",
        "/api/auth/magic-link/verify/",
        "/api/auth/magic-link/verify-code/",
        "/api/org/",
        "/admin/",
        "/swagger-ui/",
        "/api/schema/",
        # Public CSAT survey link (Tier 2 csat) — anonymous, sets RLS
        # context manually inside the view from the survey's own org_id.
        "/api/public/csat/",
    ]

    # Paths that require org context but must NOT be wrapped in a request-wide
    # transaction. These return streaming/long-lived responses whose body is
    # produced AFTER the view returns — so a request-wide transaction would
    # already have committed (dropping the transaction-local RLS GUC) before the
    # body runs its queries. Each such view sets its own transaction-local
    # context around its generator instead (or, like the SSE stream, does no
    # ORM at all).
    NON_ATOMIC_PATHS = [
        "/api/notifications/stream/",
        "/api/cases/analytics/export/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Enforce org context on non-exempt, resolvable paths.
        if not self._is_exempt(request.path):
            # Skip check for URLs that don't resolve (let Django return 404)
            from django.urls import resolve
            from django.urls.exceptions import Resolver404

            try:
                resolve(request.path)
            except Resolver404:
                return self.get_response(request)

            if not hasattr(request, "org") or request.org is None:
                return JsonResponse(
                    {"detail": "Organization context is required. Please login again."},
                    status=403,
                )

        org = getattr(request, "org", None)
        # Nothing to scope (exempt/anonymous paths), or a streaming endpoint
        # that manages its own short-lived context: don't open a request-wide
        # transaction.
        if org is None or self._is_non_atomic(request.path):
            return self.get_response(request)

        # Wrap the whole request in ONE transaction and set the RLS GUC
        # transaction-locally (is_local=True) as its first statement.
        # Transaction scope binds the value to THIS transaction and reverts it
        # on COMMIT/ROLLBACK, so it can never persist onto a backend that a
        # connection pooler (PgBouncer transaction mode) later hands to another
        # tenant. No manual reset is needed — that is the whole point.
        with transaction.atomic():
            self._set_org_context(str(org.id))
            return self.get_response(request)

    def _is_exempt(self, path):
        """Check if path is exempt from org context requirement."""
        return any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS)

    def _is_non_atomic(self, path):
        """Check if path must not be wrapped in a request-wide transaction."""
        return any(path.startswith(p) for p in self.NON_ATOMIC_PATHS)

    def _set_org_context(self, org_id):
        """Set app.current_org transaction-locally for the current transaction.

        Must be called inside an open transaction (is_local=True only persists
        until COMMIT/ROLLBACK). No-ops on non-PostgreSQL backends (the SQLite
        test backend has no set_config(); RLS is a Postgres-only feature).
        """
        if connection.vendor != "postgresql":
            return
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.current_org', %s, true)", [org_id])


# SQL to enable RLS on all org-scoped tables
RLS_SETUP_SQL = """
-- Enable RLS on main tables
-- Run this after all org-scoped tables are identified

-- Example for leads table:
-- ALTER TABLE lead ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE lead FORCE ROW LEVEL SECURITY;  -- Apply to table owner too
-- CREATE POLICY org_isolation ON lead
--   USING (org_id = NULLIF(current_setting('app.current_org', true), '')::uuid);

-- Tables that need RLS policies:
-- lead, accounts, contacts, opportunity, cases, tasks, invoices,
-- comment, attachments, document, teams, activity, tags, address,
-- api_settings, board, board_column, board_task, board_member

-- Note: Use NULLIF to handle empty string when context is not set
-- This makes the policy return no rows when context is not set (fail-safe)
"""
