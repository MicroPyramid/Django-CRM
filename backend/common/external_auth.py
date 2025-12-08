import logging

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from common.models import Org, Profile

logger = logging.getLogger(__name__)


class APIKeyAuthentication(BaseAuthentication):
    """
    API Key authentication for programmatic/external access.

    Authenticates requests with 'Token' header containing an organization API key.
    This is used for service-to-service or programmatic access to the API.

    Usage:
        curl -H "Token: <org_api_key>" https://api.example.com/endpoint/
    """

    def authenticate(self, request):
        api_key = request.headers.get("Token")
        if not api_key:
            return None  # Let other auth classes handle this request

        try:
            organization = Org.objects.get(api_key=api_key, is_active=True)

            # Get an admin profile for this org to act as the authenticated user
            profile = Profile.objects.filter(
                org=organization, role="ADMIN", is_active=True
            ).first()

            if not profile:
                logger.error(f"No active admin profile found for org {organization.id}")
                raise AuthenticationFailed("Invalid API Key configuration")

            # Set org context on request for downstream use
            request.profile = profile
            request.org = organization
            request.META["org"] = str(organization.id)

            logger.debug(f"API key authenticated: org={organization.id}")
            return (profile.user, None)

        except Org.DoesNotExist:
            logger.warning("Invalid API key attempted")
            raise AuthenticationFailed("Invalid API Key")


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
