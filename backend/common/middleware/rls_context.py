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

from django.db import connection

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
                # Set the session variable
                cursor.execute(
                    "SELECT set_config('app.current_org', %s, true)", [org_id]
                )
                logger.debug(f"Set RLS context: app.current_org = {org_id}")

        except Exception as e:
            # RLS might not be configured - log but don't fail
            logger.debug(f"Could not set RLS context: {e}")

    def _reset_org_context(self):
        """
        Reset the PostgreSQL session variable after request.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('app.current_org', '', true)")
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
        "/api/auth/login/",
        "/api/auth/register/",
        "/api/auth/refresh-token/",
        "/api/auth/me/",
        "/api/auth/switch-org/",
        "/api/auth/google/",
        "/api/org/",
        "/admin/",
        "/swagger-ui/",
        "/api/schema/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if path requires org context
        if not self._is_exempt(request.path):
            # Skip check for URLs that don't resolve (let Django return 404)
            from django.urls import resolve
            from django.urls.exceptions import Resolver404

            try:
                resolve(request.path)
            except Resolver404:
                return self.get_response(request)

            if not hasattr(request, "org") or request.org is None:
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(
                    "Organization context is required. Please login again."
                )

        # Set org context
        self._set_org_context(request)

        response = self.get_response(request)

        # Reset context
        self._reset_org_context()

        return response

    def _is_exempt(self, path):
        """Check if path is exempt from org context requirement."""
        return any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS)

    def _set_org_context(self, request):
        """Set PostgreSQL session variable."""
        if not hasattr(request, "org") or request.org is None:
            return

        org_id = str(request.org.id)

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT set_config('app.current_org', %s, true)", [org_id]
                )
        except Exception as e:
            logger.warning(f"Failed to set RLS context: {e}")

    def _reset_org_context(self):
        """Reset PostgreSQL session variable."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('app.current_org', '', true)")
        except Exception:
            pass


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
