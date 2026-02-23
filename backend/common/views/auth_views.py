import json
import logging
import secrets
import uuid
from datetime import timedelta

import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer

from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from common import serializer
from common.models import Org, Profile, User
from common.serializer import OrgAwareRefreshToken

logger = logging.getLogger(__name__)


class GoogleOAuthCallbackView(APIView):
    """
    Handle Google OAuth authorization code exchange with PKCE.
    """

    permission_classes = []
    authentication_classes = []

    @extend_schema(
        tags=["auth"],
        request=inline_serializer(
            name="GoogleOAuthRequest",
            fields={
                "code": serializers.CharField(),
                "code_verifier": serializers.CharField(),
                "redirect_uri": serializers.CharField(),
            },
        ),
        responses={
            200: inline_serializer(
                name="GoogleOAuthResponse",
                fields={
                    "access_token": serializers.CharField(),
                    "refresh_token": serializers.CharField(),
                    "user": serializers.DictField(),
                },
            )
        },
    )
    def post(self, request):
        import base64

        from django.utils import timezone

        code = request.data.get("code")
        code_verifier = request.data.get("code_verifier")
        redirect_uri = request.data.get("redirect_uri")

        if not all([code, code_verifier, redirect_uri]):
            return Response(
                {"error": "Missing required parameters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Exchange code for tokens with Google
        try:
            token_response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                    "code_verifier": code_verifier,
                },
                timeout=30,
            )
        except requests.RequestException:
            return Response(
                {"error": "Failed to communicate with Google"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if token_response.status_code != 200:
            error_data = token_response.json() if token_response.content else {}
            return Response(
                {"error": error_data.get("error_description", "Token exchange failed")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_data = token_response.json()
        id_token = token_data.get("id_token")
        if not id_token:
            return Response(
                {"error": "No ID token received"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Decode ID token payload (no verification needed - we just got it from Google over HTTPS)
        try:
            payload_part = id_token.split(".")[1]
            # Add padding if needed
            payload_part += "=" * (4 - len(payload_part) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_part))
            email = payload.get("email")
            picture = payload.get("picture", "")
        except (IndexError, ValueError, json.JSONDecodeError):
            return Response(
                {"error": "Invalid ID token format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not email:
            return Response(
                {"error": "No email in token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get or create user
        created = False
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create(
                email=email,
                profile_pic=picture,
                password=make_password(secrets.token_urlsafe(32)),
            )
            created = True

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        if created:
            from common.tasks import send_welcome_email

            send_welcome_email.delay(str(user.id))

        # Generate JWT tokens (with user info embedded)
        token = OrgAwareRefreshToken.for_user_and_org(user, None)

        return Response(
            {
                "access_token": str(token.access_token),
                "refresh_token": str(token),
                "user": {"id": str(user.id), "email": user.email},
            }
        )


class GoogleIdTokenView(APIView):
    """
    Handle Google Sign-In from mobile apps using ID token.
    Mobile app sends Google ID token, backend verifies and returns JWT.
    """

    permission_classes = []
    authentication_classes = []

    @extend_schema(
        tags=["auth"],
        request=inline_serializer(
            name="GoogleIdTokenRequest",
            fields={"idToken": serializers.CharField()},
        ),
        responses={
            200: inline_serializer(
                name="GoogleIdTokenResponse",
                fields={
                    "JWTtoken": serializers.CharField(),
                    "user": serializers.DictField(),
                    "organizations": serializers.ListField(),
                },
            )
        },
    )
    def post(self, request):
        from django.utils import timezone

        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        id_token_str = request.data.get("idToken")
        if not id_token_str:
            return Response(
                {"error": "Missing idToken"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the ID token with Google
        try:
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
            email = idinfo.get("email")
            picture = idinfo.get("picture", "")
        except ValueError:
            logger.warning("Google OAuth token validation failed", exc_info=True)
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not email:
            return Response(
                {"error": "No email in token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get or create user
        user, _created = User.objects.get_or_create(
            email=email,
            defaults={
                "profile_pic": picture,
                "password": make_password(secrets.token_urlsafe(32)),
            },
        )
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        # Get user's organizations
        profiles = Profile.objects.filter(user=user).select_related("org")
        organizations = [
            {
                "id": str(p.org.id),
                "name": p.org.name,
                "role": p.role,
            }
            for p in profiles
        ]

        # Generate JWT token
        token = OrgAwareRefreshToken.for_user_and_org(user, None)

        return Response(
            {
                "JWTtoken": str(token.access_token),
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": email.split("@")[0],
                    "profileImage": user.profile_pic,
                },
                "organizations": organizations,
            }
        )


class LoginView(APIView):
    """
    Login with email and password, returns JWT tokens
    """

    permission_classes = []
    authentication_classes = []

    @extend_schema(
        description="Login with email and password",
        request=serializer.LoginSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "access_token": {"type": "string"},
                    "refresh_token": {"type": "string"},
                    "user": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "email": {"type": "string"},
                            "organizations": {"type": "array"},
                        },
                    },
                },
            }
        },
    )
    def post(self, request):
        from django.utils import timezone

        from common.audit_log import audit_log

        serializer_obj = serializer.LoginSerializer(data=request.data)
        if serializer_obj.is_valid():
            user = serializer_obj.validated_data["user"]

            # Update last_login timestamp
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])

            # Get user's organizations
            profiles = Profile.objects.filter(user=user, is_active=True)

            # Get the default org (first org or from request)
            org_id = request.data.get("org_id")
            default_org = None

            if org_id:
                try:
                    uuid.UUID(str(org_id))
                except (ValueError, AttributeError):
                    return Response(
                        {"error": "org_id must be a valid UUID"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                # Use specified org if user has access
                try:
                    profile = profiles.get(org_id=org_id)
                    default_org = profile.org
                except Profile.DoesNotExist:
                    audit_log.login_failure(
                        user.email, f"No access to org {org_id}", request
                    )
                    return Response(
                        {
                            "error": "User does not have access to specified organization"
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
            elif profiles.exists():
                # Use first available org
                profile = profiles.first()
                default_org = profile.org

            # Generate JWT tokens with org context (include profile for role)
            if default_org:
                token = OrgAwareRefreshToken.for_user_and_org(
                    user, default_org, profile
                )
            else:
                # User has no orgs - generate token without org context (but with user info)
                token = OrgAwareRefreshToken.for_user_and_org(user, None)

            # Audit log successful login
            audit_log.login_success(user, default_org, request)

            # Get user details with organizations
            user_serializer = serializer.UserDetailSerializer(user)

            response_data = {
                "access_token": str(token.access_token),
                "refresh_token": str(token),
                "user": user_serializer.data,
            }

            # Include current org info if available
            if default_org:
                response_data["current_org"] = {
                    "id": str(default_org.id),
                    "name": default_org.name,
                }

            return Response(response_data, status=status.HTTP_200_OK)

        # Log failed login
        email = request.data.get("email", "unknown")
        audit_log.login_failure(email, str(serializer_obj.errors), request)
        return Response(serializer_obj.errors, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    """
    Get current authenticated user details
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Get current authenticated user with organizations",
        responses={200: serializer.UserDetailSerializer},
    )
    def get(self, request):
        user_serializer = serializer.UserDetailSerializer(request.user)
        return Response(user_serializer.data, status=status.HTTP_200_OK)


class OrgAwareTokenRefreshView(APIView):
    """
    Custom token refresh that validates org membership.

    When refreshing a token, this view:
    1. Validates the refresh token
    2. Checks that user still has access to the org in the token
    3. Issues new tokens with the same org context

    If membership was revoked, returns 403 and user must login again.
    """

    permission_classes = []
    authentication_classes = []

    @extend_schema(
        description="Refresh access token with org membership validation",
        request=inline_serializer(
            name="OrgAwareTokenRefreshRequest",
            fields={"refresh": serializers.CharField(help_text="Refresh token")},
        ),
        responses={
            200: inline_serializer(
                name="OrgAwareTokenRefreshResponse",
                fields={
                    "access": serializers.CharField(),
                    "refresh": serializers.CharField(),
                },
            )
        },
    )
    def post(self, request):
        from rest_framework_simplejwt.exceptions import TokenError
        from rest_framework_simplejwt.tokens import RefreshToken as BaseRefreshToken

        from common.audit_log import audit_log

        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Decode and validate refresh token
            token = BaseRefreshToken(refresh_token)
            user_id = token["user_id"]
            org_id = token.get("org_id")

            # Get user
            user = User.objects.get(id=user_id)

            if not user.is_active:
                return Response(
                    {"error": "User account is disabled"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # If token has org context, validate membership
            if org_id:
                try:
                    profile = Profile.objects.get(
                        user=user, org_id=org_id, is_active=True
                    )
                    org = profile.org
                except Profile.DoesNotExist:
                    # Membership revoked - user must login again
                    audit_log.token_revoked(
                        user, None, f"Membership revoked for org {org_id}", request
                    )
                    return Response(
                        {
                            "error": "Organization membership revoked. Please login again."
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

                # Generate new tokens with same org context (include profile for role)
                new_token = OrgAwareRefreshToken.for_user_and_org(user, org, profile)
                audit_log.token_refresh(user, org, request)
            else:
                # No org context - refresh with user info only
                new_token = OrgAwareRefreshToken.for_user_and_org(user, None)
                audit_log.token_refresh(user, None, request)

            return Response(
                {"access": str(new_token.access_token), "refresh": str(new_token)},
                status=status.HTTP_200_OK,
            )

        except TokenError:
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_401_UNAUTHORIZED
            )


class OrgSwitchView(APIView):
    """
    Switch to a different organization and get new JWT tokens.

    This endpoint validates that the user has access to the target
    organization and issues new tokens with the org_id claim.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Switch to a different organization and get new JWT tokens",
        request=inline_serializer(
            name="OrgSwitchRequest",
            fields={
                "org_id": serializers.UUIDField(help_text="Target organization ID")
            },
        ),
        responses={
            200: inline_serializer(
                name="OrgSwitchResponse",
                fields={
                    "access_token": serializers.CharField(),
                    "refresh_token": serializers.CharField(),
                    "current_org": serializers.DictField(),
                    "profile": serializers.DictField(),
                },
            )
        },
    )
    def post(self, request):
        from common.audit_log import audit_log

        org_id = request.data.get("org_id")

        if not org_id:
            return Response(
                {"error": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uuid.UUID(str(org_id))
        except (ValueError, AttributeError):
            return Response(
                {"error": "org_id must be a valid UUID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get current org for audit logging
        from_org = getattr(request, "org", None)

        # Validate user has access to the target org
        try:
            profile = Profile.objects.get(
                user=request.user, org_id=org_id, is_active=True
            )
        except Profile.DoesNotExist:
            audit_log.permission_denied(
                request.user, from_org, "ORG_SWITCH", f"org:{org_id}", request
            )
            return Response(
                {"error": "User does not have access to this organization"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Generate new tokens with the target org (include profile for role)
        token = OrgAwareRefreshToken.for_user_and_org(
            request.user, profile.org, profile
        )

        # Audit log the org switch
        audit_log.org_switch(request.user, from_org, profile.org, request)

        return Response(
            {
                "access_token": str(token.access_token),
                "refresh_token": str(token),
                "current_org": {"id": str(profile.org.id), "name": profile.org.name},
                "profile": {
                    "id": str(profile.id),
                    "role": profile.role,
                    "is_organization_admin": profile.is_organization_admin,
                },
            },
            status=status.HTTP_200_OK,
        )


class MagicLinkRequestView(APIView):
    """
    Request a magic link for passwordless login/registration.
    Always returns 200 to prevent email enumeration.
    """

    permission_classes = []
    authentication_classes = []

    @extend_schema(
        tags=["auth"],
        request=serializer.MagicLinkRequestSerializer,
        responses={200: inline_serializer(
            name="MagicLinkRequestResponse",
            fields={"message": serializers.CharField()},
        )},
    )
    def post(self, request):
        from common.models import MagicLinkToken
        from common.tasks import send_magic_link_email

        generic_response = Response(
            {"message": "If this email is valid, you will receive a sign-in link."},
            status=status.HTTP_200_OK,
        )

        serializer_obj = serializer.MagicLinkRequestSerializer(data=request.data)
        if not serializer_obj.is_valid():
            return generic_response

        email = serializer_obj.validated_data["email"].lower()

        # Rate limit: max 5 tokens per email per hour
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_count = MagicLinkToken.objects.filter(
            email=email, created_at__gte=one_hour_ago
        ).count()
        if recent_count >= 5:
            return generic_response

        # Invalidate any existing unused tokens for this email
        MagicLinkToken.objects.filter(email=email, is_used=False).update(is_used=True)

        # Create new token
        token_obj = MagicLinkToken.objects.create(
            email=email,
            token=secrets.token_hex(32),
            expires_at=timezone.now() + timedelta(minutes=10),
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        # Send email via Celery
        send_magic_link_email.delay(str(token_obj.id))

        return Response(
            {"message": "If this email is valid, you will receive a sign-in link."},
            status=status.HTTP_200_OK,
        )


class MagicLinkVerifyView(APIView):
    """
    Verify a magic link token and return JWT tokens.
    Creates a new user if the email doesn't exist.
    """

    permission_classes = []
    authentication_classes = []

    @extend_schema(
        tags=["auth"],
        request=serializer.MagicLinkVerifySerializer,
        responses={
            200: inline_serializer(
                name="MagicLinkVerifyResponse",
                fields={
                    "access_token": serializers.CharField(),
                    "refresh_token": serializers.CharField(),
                    "user": serializers.DictField(),
                },
            )
        },
    )
    def post(self, request):
        from django.contrib.auth.hashers import make_password

        from common.audit_log import audit_log
        from common.models import MagicLinkToken

        serializer_obj = serializer.MagicLinkVerifySerializer(data=request.data)
        if not serializer_obj.is_valid():
            return Response(
                {"error": "Invalid request"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_value = serializer_obj.validated_data["token"]

        # Opportunistic cleanup: delete expired tokens
        MagicLinkToken.objects.filter(expires_at__lt=timezone.now()).delete()

        # Atomically mark token as used (prevents race condition)
        updated = MagicLinkToken.objects.filter(
            token=token_value,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).update(is_used=True, used_at=timezone.now())

        if not updated:
            return Response(
                {"error": "Invalid or expired link"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_obj = MagicLinkToken.objects.get(token=token_value)

        # Get or create user
        email = token_obj.email
        created = False
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create(
                email=email,
                password=make_password(secrets.token_urlsafe(32)),
                is_active=True,
            )
            created = True

        if created:
            from common.tasks import send_welcome_email

            send_welcome_email.delay(str(user.id))

        # Update last_login
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        # Get user's organizations
        profiles = Profile.objects.filter(user=user, is_active=True)
        default_org = None
        profile = None

        if profiles.exists():
            profile = profiles.first()
            default_org = profile.org

        # Generate JWT tokens (same as LoginView)
        if default_org:
            token = OrgAwareRefreshToken.for_user_and_org(user, default_org, profile)
        else:
            token = OrgAwareRefreshToken.for_user_and_org(user, None)

        # Audit log
        audit_log.login_success(user, default_org, request)

        # Build response (same shape as LoginView)
        user_serializer = serializer.UserDetailSerializer(user)
        response_data = {
            "access_token": str(token.access_token),
            "refresh_token": str(token),
            "user": user_serializer.data,
        }

        if default_org:
            response_data["current_org"] = {
                "id": str(default_org.id),
                "name": default_org.name,
            }

        return Response(response_data, status=status.HTTP_200_OK)
