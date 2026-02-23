import logging

from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import AuthenticationFailed

from common.models import Org, Profile

logger = logging.getLogger(__name__)


class GetProfileAndOrg:
    """
    Middleware to extract and validate organization context from JWT tokens.

    SECURITY: This middleware validates org_id from the SIGNED JWT token,
    not from client-provided headers. This prevents org spoofing attacks.

    The org context is cryptographically verified as part of the JWT signature.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        return self.get_response(request)

    def process_request(self, request):
        # Skip JWT validation for authentication endpoints that don't need org context
        auth_skip_paths = [
            "/api/auth/login/",
            "/api/auth/google/",
            "/api/auth/register/",
            "/api/auth/refresh-token/",
            "/api/auth/me/",
            "/api/auth/switch-org/",
            "/api/auth/magic-link/request/",
            "/api/auth/magic-link/verify/",
        ]
        if request.path in auth_skip_paths:
            return

        # Initialize request attributes
        request.profile = None
        request.org = None

        # Try JWT token first (primary authentication)
        if request.headers.get("Authorization"):
            self._process_jwt_auth(request)
            return

        # Fall back to API key authentication
        api_key = request.headers.get("Token")
        if api_key:
            self._process_api_key_auth(request, api_key)
            return

    def _process_jwt_auth(self, request):
        """
        Process JWT authentication and extract org context from token.

        SECURITY: Org ID is extracted from the signed JWT payload, not headers.
        """
        from rest_framework_simplejwt.tokens import AccessToken

        try:
            auth_header = request.headers.get("Authorization")
            token_value = auth_header.split(" ")[1]

            # Validate and decode token
            access_token = AccessToken(token_value)
            user_id = access_token["user_id"]

            # Get org_id from JWT claim (SECURE - cryptographically signed)
            org_id = access_token.get("org_id")

            if not org_id:
                # Token doesn't have org context - this is allowed for some endpoints
                # like /api/auth/me/ or initial login
                logger.debug("JWT token for user %s has no org_id claim", user_id)
                return

            # Validate user membership in the org
            try:
                profile = Profile.objects.select_related("org").get(
                    user_id=user_id, org_id=org_id, is_active=True
                )
                request.profile = profile
                request.org = profile.org
                logger.debug("Set org context from JWT: user=%s, org=%s", user_id, org_id)

            except Profile.DoesNotExist as exc:
                # User doesn't have access to this org anymore
                # This can happen if membership was revoked after token was issued
                logger.warning(
                    "User %s no longer has access to org %s. Token may be stale.",
                    user_id,
                    org_id,
                )
                raise PermissionDenied(
                    "You no longer have access to this organization. "
                    "Please login again."
                ) from exc

        except (IndexError, KeyError) as e:
            logger.warning("Malformed Authorization header: %s", e)
            # Let DRF authentication handle this
            return

        except Exception as e:
            logger.warning("JWT validation failed: %s", e)
            # Let DRF authentication handle invalid tokens
            return

    def _process_api_key_auth(self, request, api_key):
        """Process API key authentication."""
        try:
            organization = Org.objects.get(api_key=api_key, is_active=True)

            # Get an admin profile for this org
            profile = Profile.objects.filter(
                org=organization, role="ADMIN", is_active=True
            ).first()

            if not profile:
                logger.error("No active admin profile found for org %s", organization.id)
                raise AuthenticationFailed("Invalid API Key configuration")

            request.profile = profile
            request.org = organization
            request.META["org"] = str(organization.id)

            logger.debug("Set org context from API key: org=%s", organization.id)

        except Org.DoesNotExist as exc:
            logger.warning("Invalid API key attempted")
            raise AuthenticationFailed("Invalid API Key") from exc
