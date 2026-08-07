import logging

from django.utils import timezone
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from common.models import PersonalAccessToken

logger = logging.getLogger(__name__)

PAT_PREFIX = "bcrm_pat_"


def _extract_raw(request):
    """Pull a bcrm_pat_ token from Authorization: Bearer or Token header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        candidate = auth[len("Bearer ") :].strip()
        if candidate.startswith(PAT_PREFIX):
            return candidate
    token = request.headers.get("Token", "")
    if token.startswith(PAT_PREFIX):
        return token
    return None


def resolve_valid_pat(raw):
    """Look up and validate a raw PAT.

    Returns the PersonalAccessToken (with profile/user/org pre-fetched) or
    raises AuthenticationFailed. Shared by the GetProfileAndOrg middleware
    (which must set org context before RequireOrgContext runs) and the DRF
    PATAuthentication class, so the lookup/validation logic lives in one place.
    """
    try:
        pat = PersonalAccessToken.objects.select_related(
            "profile", "profile__user", "org"
        ).get(token_hash=PersonalAccessToken.hash_token(raw))
    except PersonalAccessToken.DoesNotExist as exc:
        logger.warning("Invalid PAT attempted")
        raise AuthenticationFailed("Invalid token") from exc
    if not pat.is_valid():
        raise AuthenticationFailed("Token revoked or expired")
    if not pat.profile.is_active or not pat.org.is_active:
        raise AuthenticationFailed("Token owner or org is inactive")
    return pat


class PATAuthentication(BaseAuthentication):
    """Authenticate an agent AS the token's owning Profile (inherits role+org)."""

    def authenticate(self, request):
        raw = _extract_raw(request)
        if not raw:
            return None  # Not a PAT. Let JWT / org-key auth handle it.

        # The GetProfileAndOrg middleware resolves the PAT first (so org
        # context is set before RequireOrgContext runs) and stashes it on the
        # request. Reuse it to avoid a second DB lookup and a double
        # last_used_at write. Fall back to resolving here for any code path
        # that bypasses the middleware (e.g. RequestFactory unit tests).
        pat = getattr(request, "_pat", None)
        if pat is None:
            pat = resolve_valid_pat(raw)

        profile = pat.profile

        request.profile = profile
        request.org = pat.org
        request.META["org"] = str(pat.org.id)
        request.META["pat_token_id"] = str(pat.id)

        now = timezone.now()
        if pat.last_used_at is None or (now - pat.last_used_at).total_seconds() > 60:
            PersonalAccessToken.objects.filter(pk=pat.pk).update(last_used_at=now)
            pat.last_used_at = now

        return (profile.user, pat)


class PATAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "common.pat_auth.PATAuthentication"
    name = "PersonalAccessToken"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "description": "Personal access token (bcrm_pat_…) for script and agent access",
        }
