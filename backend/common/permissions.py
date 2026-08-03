"""
Custom Permission Classes for Multi-Tenancy Security

These permission classes enforce organization context and access control
across all API endpoints.
"""

from rest_framework import permissions


class HasOrgContext(permissions.BasePermission):
    """
    Permission class that requires valid organization context.

    This should be used on all endpoints that require org-scoped data access.
    It verifies that:
    1. User is authenticated
    2. request.profile is set (from middleware)
    3. request.org is set (from JWT or API key)

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, HasOrgContext]
    """

    message = "Organization context is required. Please login again."

    def has_permission(self, request, view):
        # Must have profile set by middleware
        if not hasattr(request, "profile") or request.profile is None:
            return False

        # Must have org set
        if not hasattr(request, "org") or request.org is None:
            return False

        # Profile must be active
        if not request.profile.is_active:
            return False

        return True


class IsOrgAdmin(permissions.BasePermission):
    """
    Permission class that requires user to be an organization admin.

    Usage:
        class AdminOnlyView(APIView):
            permission_classes = [IsAuthenticated, HasOrgContext, IsOrgAdmin]
    """

    message = "You must be an organization administrator to perform this action."

    def has_permission(self, request, view):
        if not hasattr(request, "profile") or request.profile is None:
            return False

        return request.profile.role == "ADMIN" or request.profile.is_organization_admin


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission class for platform-level super admins.

    Super admin is an explicit, deliberately granted flag on the user record
    (``User.is_superuser``), never inferred from the email address. Deriving it
    from an email domain would hand platform-wide access: every org, every
    user. To anyone who can obtain an account at that domain, turning an
    ordinary signup into vertical privilege escalation.

    Grant it with ``manage.py createsuperuser``, the Django admin, or another
    audited path, not by handing out an email address.
    """

    message = "Super admin access required."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        return bool(user.is_active and user.is_superuser)
