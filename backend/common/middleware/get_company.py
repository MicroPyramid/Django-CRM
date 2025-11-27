import jwt
import logging
from django.conf import settings
from django.contrib.auth import logout
from django.core.exceptions import ValidationError, PermissionDenied
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from crum import get_current_user
from django.utils.functional import SimpleLazyObject

from common.models import Org, Profile, User

logger = logging.getLogger(__name__)


def get_actual_value(request):
    if request.user is None:
        return None
    return request.user


class GetProfileAndOrg(object):
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
            '/api/auth/login/',
            '/api/auth/google/',
            '/api/auth/register/',
            '/api/auth/refresh-token/',
            '/api/auth/me/',
            '/api/auth/switch-org/',
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
        api_key = request.headers.get('Token')
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
            user_id = access_token['user_id']

            # Get org_id from JWT claim (SECURE - cryptographically signed)
            org_id = access_token.get('org_id')

            if not org_id:
                # Token doesn't have org context - this is allowed for some endpoints
                # like /api/auth/me/ or initial login
                logger.debug(f"JWT token for user {user_id} has no org_id claim")
                return

            # Validate user membership in the org
            try:
                profile = Profile.objects.select_related('org').get(
                    user_id=user_id,
                    org_id=org_id,
                    is_active=True
                )
                request.profile = profile
                request.org = profile.org
                logger.debug(f"Set org context from JWT: user={user_id}, org={org_id}")

            except Profile.DoesNotExist:
                # User doesn't have access to this org anymore
                # This can happen if membership was revoked after token was issued
                logger.warning(
                    f"User {user_id} no longer has access to org {org_id}. "
                    "Token may be stale."
                )
                raise PermissionDenied(
                    "You no longer have access to this organization. "
                    "Please login again."
                )

        except (IndexError, KeyError) as e:
            logger.warning(f"Malformed Authorization header: {e}")
            # Let DRF authentication handle this
            return

        except Exception as e:
            logger.warning(f"JWT validation failed: {e}")
            # Let DRF authentication handle invalid tokens
            return

    def _process_api_key_auth(self, request, api_key):
        """
        Process API key authentication.

        Note: API keys are scoped to a specific org and use an admin profile.
        TODO: Create dedicated API key model with granular permissions.
        """
        try:
            organization = Org.objects.get(api_key=api_key, is_active=True)

            # Get an admin profile for this org
            profile = Profile.objects.filter(
                org=organization,
                role="ADMIN",
                is_active=True
            ).first()

            if not profile:
                logger.error(f"No active admin profile found for org {organization.id}")
                raise AuthenticationFailed('Invalid API Key configuration')

            request.profile = profile
            request.org = organization
            request.META['org'] = str(organization.id)

            logger.debug(f"Set org context from API key: org={organization.id}")

        except Org.DoesNotExist:
            logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
            raise AuthenticationFailed('Invalid API Key')
