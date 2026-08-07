import logging

from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from common import scopes
from common.models import Org, Profile

logger = logging.getLogger(__name__)


class APIKeyAuthentication(BaseAuthentication):
    """
    API Key authentication for programmatic/external access.

    Authenticates requests with 'Token' header containing an organization API key.
    This is used for service-to-service or programmatic access to the API.

    Usage:
        curl -H "Token: <org_api_key>" https://api.example.com/endpoint/

    The same two limits the middleware applies are repeated here, on purpose.
    This class duplicates the middleware's key resolution, and a request can
    reach DRF authentication by a path the middleware skipped (its own exempt
    list, a test using RequestFactory, or a view mounted outside `/api/`).
    Guarding one copy and not the other would mean the DRF layer still admits
    exactly what the middleware just refused. See
    `common.middleware.get_company.GetProfileAndOrg._process_api_key_auth` for
    what the limits are and why.
    """

    def authenticate(self, request):
        api_key = request.headers.get("Token")
        if not api_key:
            return None  # Let other auth classes handle this request

        if not getattr(settings, "ORG_API_KEY_AUTH_ENABLED", True):
            raise AuthenticationFailed(
                "Organization API key authentication is disabled on this "
                "deployment. Use a personal access token."
            )

        denial = scopes.check_request(
            scopes.ORG_API_KEY_SCOPES, request.method, request.path
        )
        if denial is not None:
            raise AuthenticationFailed(denial)

        try:
            organization = Org.objects.get(api_key=api_key, is_active=True)

            # Get an admin profile for this org to act as the authenticated user
            profile = Profile.objects.filter(
                org=organization, role="ADMIN", is_active=True
            ).first()

            if not profile:
                logger.error(
                    "No active admin profile found for org %s", organization.id
                )
                raise AuthenticationFailed("Invalid API Key configuration")

            # Set org context on request for downstream use
            request.profile = profile
            request.org = organization
            request.META["org"] = str(organization.id)

            logger.debug("API key authenticated: org=%s", organization.id)
            return (profile.user, None)

        except Org.DoesNotExist as exc:
            logger.warning("Invalid API key attempted")
            raise AuthenticationFailed("Invalid API Key") from exc


class APIKeyAuthenticationScheme(OpenApiAuthenticationExtension):
    """OpenAPI schema extension for API Key authentication."""

    target_class = "common.external_auth.APIKeyAuthentication"
    name = "APIKeyAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Token",
            "description": "Organization API key for programmatic access",
        }
