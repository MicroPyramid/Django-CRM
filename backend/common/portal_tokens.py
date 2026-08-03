"""Anonymous portal token → org resolution.

The public portal endpoints (invoice/estimate links, CSAT surveys) are the only
anonymous, org-less requests that must read org-scoped rows. RLS hides those
rows under an empty context, so before the resource query can run the view has
to learn the org from the token alone. ``common.models.PortalAccessToken`` is
the unscoped lookup that makes that possible; this module is the thin API over
it.

The lookup key is always ``sha256(url_token)``:

* invoice / estimate. The URL token is the raw ``public_token``;
* CSAT: the URL token is the signed token, and ``cases.tasks.hash_csat_token``
  already stores its SHA-256 as ``csat_survey.token_hash``.

Registration is called from the same place each token is minted, so the lookup
never drifts from the source of truth. Resolution is deliberately side-effect
free apart from returning the org id. The caller sets the RLS context.
"""

import hashlib

from common.models import PortalAccessToken


def portal_token_hash(url_token: str) -> str:
    """SHA-256 hex digest of a raw URL token. The lookup key."""
    return hashlib.sha256(url_token.encode("utf-8")).hexdigest()


def register_portal_token(url_token, org_id, resource_type, resource_id) -> None:
    """Upsert the ``token_hash → org`` row for a freshly-minted URL token.

    Safe to call under any RLS context: ``PortalAccessToken`` carries no policy.
    A no-op when the token or org is missing (nothing to resolve later).
    """
    if not url_token or not org_id:
        return
    register_portal_token_hash(
        portal_token_hash(url_token), org_id, resource_type, resource_id
    )


def register_portal_token_hash(token_hash, org_id, resource_type, resource_id) -> None:
    """Upsert by pre-computed hash, for callers that only store the hash (CSAT)."""
    if not token_hash or not org_id:
        return
    PortalAccessToken.objects.update_or_create(
        token_hash=token_hash,
        defaults={
            "org_id": org_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
        },
    )


def resolve_portal_org(url_token, resource_type=None):
    """Resolve the org id for a raw URL token, or ``None`` if unknown.

    Reads the unscoped lookup only, no org-scoped table is touched, so it works
    with an empty RLS context. When ``resource_type`` is given it must match,
    so an estimate token cannot resolve on the invoice endpoint. The caller is
    responsible for ``set_rls_context`` and for the resource query that
    re-verifies the token under RLS.
    """
    return resolve_portal_org_by_hash(portal_token_hash(url_token), resource_type)


def resolve_portal_org_by_hash(token_hash, resource_type=None):
    """As :func:`resolve_portal_org`, for a caller that already hashed the token."""
    qs = PortalAccessToken.objects.filter(token_hash=token_hash)
    if resource_type is not None:
        qs = qs.filter(resource_type=resource_type)
    row = qs.values_list("org_id", flat=True).first()
    return str(row) if row else None
