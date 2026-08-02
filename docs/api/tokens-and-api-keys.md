# Tokens and API keys

Two credential types exist alongside the JWT session described in
[Authentication](authentication.md), for callers that need to authenticate without a browser or an
interactive sign-in: personal access tokens and the per-org API key. This page documents the CRUD
surface for both. For what each one is, how it's resolved, and how its blast radius compares to the
others, see [Architecture: Authentication](../architecture/authentication.md#personal-access-tokens)
and [Security hardening](../self-hosting/security-hardening.md#token-surfaces).

## Personal access tokens

A personal access token (`bcrm_pat_…`, `PersonalAccessToken` in `backend/common/models.py:854-907`)
authenticates as the profile that created it and inherits that profile's role and org in full. It
carries a `scopes` field, but nothing in the request-handling code enforces it — read the model's
own comment before assuming otherwise:

```python
# NOTE: scopes are stored for forward-compatibility but are NOT enforced in
# Phase 1 — a token always inherits the owning profile's full role/permissions.
# Do not treat `scopes` as a trust boundary until enforcement lands.
```

(`backend/common/models.py:871-873`.) Set `scopes` if you like for your own bookkeeping; it does not
restrict what the token can do today.

`GET /api/profile/tokens/` (`PersonalAccessTokenListCreateView`,
`backend/common/views/pat_views.py:33-47`) lists the caller's own tokens — filtered on
`profile=request.profile` as well as `org=request.profile.org`, since this table carries no RLS
policy of its own (it's looked up by `token_hash` before any org context exists, so the explicit
filter here is the only tenant boundary, not a belt over RLS's braces):

```json
{
  "error": false,
  "tokens": [
    {
      "id": "<uuid>",
      "name": "laptop mcp",
      "token_prefix": "bcrm_pat_abc1",
      "scopes": [],
      "expires_at": null,
      "last_used_at": "2026-07-30T12:00:00Z",
      "created_at": "2026-07-01T09:00:00Z",
      "revoked_at": null
    }
  ]
}
```

`token_hash` is never serialized (`PersonalAccessTokenListSerializer`,
`backend/common/serializer.py:1054-1067`, whose `fields` is the exhaustive list above) — only
`token_prefix` identifies a token in any listing, on this endpoint or the admin one below.

## Creating and revoking

`POST /api/profile/tokens/` (same view, `:49-69`) creates a token for the caller:

```json
{"name": "laptop mcp", "scopes": [], "expires_at": null}
```

`name` is required (non-empty, at most 255 characters); `scopes`, if present, must be a list of
strings (at most 32); `expires_at` is optional, but if present must be in the future —
`validate_expires_at` rejects a past timestamp with `"expires_at must be in the future."`
(`backend/common/serializer.py:1092-1097`). On success (`201`):

```json
{
  "error": false,
  "id": "<uuid>",
  "name": "laptop mcp",
  "token_prefix": "bcrm_pat_abc1",
  "scopes": [],
  "expires_at": null,
  "last_used_at": null,
  "created_at": "2026-08-02T10:00:00Z",
  "revoked_at": null,
  "token": "bcrm_pat_abc1...<the full raw token>"
}
```

The `token` field is the only time the raw value is ever returned — it is generated, hashed, and
the plaintext discarded; there is no way to retrieve it again later, only to revoke it and create a
new one. A validation failure returns `400` with `{"error": true, "errors": {...}}`, the same shape
described in [Errors](errors.md#validation-errors).

`DELETE /api/profile/tokens/{id}/` (`PersonalAccessTokenDetailView`, `:72-86`) revokes a token —
sets `revoked_at`, it does not delete the row. It is scoped to `org=request.profile.org` **and**
`profile=request.profile` in the same lookup, so another user's token id returns `404`, not `403`:
revoking is unavailable to anyone but the token's own owner, and the lookup gives no sign a
different user's token even exists at that id. Revoking an already-revoked token is a no-op that
still returns `200`.

## Organization token oversight

`GET /api/org/tokens/` (`OrgAccessTokenListView`, `backend/common/views/pat_views.py:89-152`) is a
separate, admin-only endpoint — `permission_classes = (IsAuthenticated, HasOrgContext,
IsOrgAdmin)` — that lists every personal access token in the org, not just the caller's own. It is
deliberately kept apart from `profile/tokens/` above rather than folded into it with an
admin-widened filter, so the "a user manages only their own tokens" guard on the self-service
endpoint is never the thing that has to be loosened to support oversight:

```json
{
  "error": false,
  "tokens": [
    {
      "id": "<uuid>",
      "name": "laptop mcp",
      "token_prefix": "bcrm_pat_abc1",
      "scopes": [],
      "expires_at": null,
      "last_used_at": "2026-07-30T12:00:00Z",
      "created_at": "2026-07-01T09:00:00Z",
      "revoked_at": null,
      "owner": {"id": "<uuid>", "name": "Jane Doe", "role": "USER", "is_active": false},
      "is_live": true
    }
  ],
  "totals": {"count": 12, "live": 9, "orphaned": 2, "unused_90d": 3}
}
```

`owner.is_active: false` with `is_live: true` is the specific case this view exists to surface: a
token belonging to a profile that has since been deactivated. Deactivating a profile invalidates its
tokens as a side effect, not through any separate revocation step —
`resolve_valid_pat` (`backend/common/pat_auth.py:29-46`) checks `pat.profile.is_active` (and
`pat.org.is_active`) on every single use, so the token in the example above cannot actually
authenticate again unless the owner's profile is reactivated first. `"orphaned"` in `totals` counts
exactly these: still unrevoked (`is_live`), but dormant because their owner is gone, which is what an
admin doing offboarding cleanup would revoke explicitly with the endpoint below.

`DELETE /api/org/tokens/{id}/` (`OrgAccessTokenDetailView`, `:155-176`) revokes any token in the
admin's own org, filtered only on `org=request.profile.org` (no `profile=` filter, unlike the
self-service delete above) — an admin can revoke a colleague's token, deactivated or not. A pk from
another org still `404`s. Revoking an already-revoked token is a no-op `200`, same as the
self-service endpoint.

## Organization API keys

Each org has exactly one API key (`Org.api_key`), managed through `GET`/`POST /api/org/api-key/`
(`OrgApiKeyView`, `backend/common/views/organization_views.py:244-326`), admin-only in both
directions — checked by hand in `_admin_org_or_error` (`:255-275`) rather than an `IsOrgAdmin`
permission class, but the same rule: `request.profile.role == "ADMIN"` or
`request.profile.is_organization_admin`.

Unlike a personal access token, this key doesn't authenticate as any particular person — a request
bearing it in the `Token` header resolves to the org's first active `ADMIN` profile
(`backend/common/middleware/get_company.py:157-183`), so a leaked key is equivalent to a leaked
admin session for that org, not one user's session, and there's no way to scope it down. The org is
always taken from `request.profile.org`, never from anything client-supplied, so a caller can only
ever read or rotate their own org's key.

`GET /api/org/api-key/`:

```json
{"error": false, "api_key": "<the current key>"}
```

`POST /api/org/api-key/` rotates it — generates a new key and immediately overwrites the old one:

```json
{
  "error": false,
  "message": "API key rotated. The previous key is no longer valid.",
  "api_key": "<the new key>"
}
```

The message is not just cosmetic: the old key stops authenticating the moment this call returns,
with no grace period. A non-admin caller gets `403` with
`{"error": true, "errors": "Only organization admins can access the API key"}` from either method;
a caller with no org context at all gets `400` with
`{"error": true, "errors": "Organization context required"}`.
