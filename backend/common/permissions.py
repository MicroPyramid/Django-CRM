"""
Custom Permission Classes for Multi-Tenancy Security

These permission classes enforce organization context and access control
across all API endpoints.
"""

from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


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


class IsOrgMember(permissions.BasePermission):
    """
    Permission class that verifies user belongs to the organization.

    This is a safety check that complements the middleware validation.
    """

    message = "You are not a member of this organization."

    def has_permission(self, request, view):
        if not hasattr(request, "profile") or request.profile is None:
            return False

        if not hasattr(request, "org") or request.org is None:
            return False

        # Verify profile org matches request org
        return request.profile.org_id == request.org.id


class HasSalesAccess(permissions.BasePermission):
    """
    Permission class that requires sales module access.

    Usage:
        class LeadsView(APIView):
            permission_classes = [IsAuthenticated, HasOrgContext, HasSalesAccess]
    """

    message = "You do not have access to the sales module."

    def has_permission(self, request, view):
        if not hasattr(request, "profile") or request.profile is None:
            return False

        # Admins always have access
        if request.profile.role == "ADMIN":
            return True

        return request.profile.has_sales_access


class HasMarketingAccess(permissions.BasePermission):
    """
    Permission class that requires marketing module access.

    Usage:
        class CampaignsView(APIView):
            permission_classes = [IsAuthenticated, HasOrgContext, HasMarketingAccess]
    """

    message = "You do not have access to the marketing module."

    def has_permission(self, request, view):
        if not hasattr(request, "profile") or request.profile is None:
            return False

        # Admins always have access
        if request.profile.role == "ADMIN":
            return True

        return request.profile.has_marketing_access


class CanAccessObject(permissions.BasePermission):
    """
    Object-level permission that verifies user can access specific object.

    Checks that:
    1. Object belongs to user's organization
    2. User is assigned to object OR is admin OR created the object

    Usage:
        class LeadDetailView(APIView):
            permission_classes = [IsAuthenticated, HasOrgContext, CanAccessObject]

            def get_object(self):
                return Lead.objects.get(pk=self.kwargs['pk'])
    """

    message = "You do not have permission to access this object."

    def has_object_permission(self, request, view, obj):
        # Object must belong to same org
        if hasattr(obj, "org_id"):
            if obj.org_id != request.org.id:
                return False

        # Admins can access all objects in their org
        if request.profile.role == "ADMIN":
            return True

        # Check if user created the object
        if hasattr(obj, "created_by_id"):
            if obj.created_by_id == request.profile.user_id:
                return True

        # Check if user is assigned to the object
        if hasattr(obj, "assigned_to"):
            if request.profile in obj.assigned_to.all():
                return True

        # Check if user is in a team assigned to the object
        if hasattr(obj, "teams"):
            user_team_ids = request.profile.user_teams.values_list("id", flat=True)
            if obj.teams.filter(id__in=user_team_ids).exists():
                return True

        return False


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission class for platform-level super admins.

    Super admins are identified by @micropyramid.com email domain.
    They have access to admin panel and can manage all organizations.
    """

    message = "Super admin access required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check for super admin email domain
        return request.user.email.endswith("@micropyramid.com")


def get_org_filtered_queryset(model, request):
    """
    Helper function to get organization-filtered queryset.

    Usage:
        queryset = get_org_filtered_queryset(Lead, request)

    Args:
        model: Django model class with org field
        request: DRF request object with profile attached

    Returns:
        QuerySet filtered by organization
    """
    if not hasattr(request, "profile") or request.profile is None:
        return model.objects.none()

    return model.objects.filter(org=request.profile.org)


def validate_org_ownership(obj, request):
    """
    Helper function to validate object belongs to user's org.

    Raises PermissionDenied if object doesn't belong to user's org.

    Usage:
        lead = Lead.objects.get(pk=pk)
        validate_org_ownership(lead, request)

    Args:
        obj: Model instance with org field
        request: DRF request object

    Raises:
        PermissionDenied: If object doesn't belong to user's org
    """
    if not hasattr(request, "profile") or request.profile is None:
        raise PermissionDenied("Organization context required")

    if not hasattr(obj, "org_id"):
        return  # Object doesn't have org field

    if obj.org_id != request.profile.org_id:
        raise PermissionDenied("Object does not belong to your organization")
