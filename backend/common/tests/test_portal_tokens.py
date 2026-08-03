"""Tests for the unscoped portal token → org resolution (common.portal_tokens).

These cover the lookup layer in isolation: hashing, registration, and
resolution with the resource-type guard. RLS itself is inert on the SQLite test
backend, so the end-to-end "resolves under a non-superuser role" property is
verified separately against Postgres; here we prove the lookup returns the right
org and refuses the wrong resource type.
"""

import hashlib

import pytest

from common.models import PortalAccessToken
from common.portal_tokens import (
    portal_token_hash,
    register_portal_token,
    register_portal_token_hash,
    resolve_portal_org,
    resolve_portal_org_by_hash,
)

pytestmark = pytest.mark.django_db


def test_hash_is_sha256_of_token():
    assert portal_token_hash("abc") == hashlib.sha256(b"abc").hexdigest()


def test_register_then_resolve_round_trip(org_a):
    register_portal_token("raw-token-1", org_a.id, "estimate", org_a.id)
    assert resolve_portal_org("raw-token-1", "estimate") == str(org_a.id)


def test_resolve_unknown_token_is_none(org_a):
    assert resolve_portal_org("never-registered") is None


def test_resource_type_guard(org_a):
    """A token registered for one resource does not resolve for another."""
    register_portal_token("raw-token-2", org_a.id, "estimate", org_a.id)
    assert resolve_portal_org("raw-token-2", "estimate") == str(org_a.id)
    # An estimate token must not resolve on the invoice endpoint.
    assert resolve_portal_org("raw-token-2", "invoice") is None
    # Without a type filter it still resolves (existence lookup).
    assert resolve_portal_org("raw-token-2") == str(org_a.id)


def test_register_is_idempotent(org_a):
    register_portal_token("raw-token-3", org_a.id, "invoice", org_a.id)
    register_portal_token("raw-token-3", org_a.id, "invoice", org_a.id)
    assert (
        PortalAccessToken.objects.filter(
            token_hash=portal_token_hash("raw-token-3")
        ).count()
        == 1
    )


def test_register_by_hash_matches_csat_storage(org_a):
    """CSAT stores sha256(token) as token_hash; resolution by raw token agrees."""
    raw = "signed-csat-token"
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    register_portal_token_hash(token_hash, org_a.id, "csat", org_a.id)
    assert resolve_portal_org_by_hash(token_hash, "csat") == str(org_a.id)
    # The view resolves from the raw URL token, same key.
    assert resolve_portal_org(raw, "csat") == str(org_a.id)


def test_register_noops_on_missing_inputs(org_a):
    register_portal_token("", org_a.id, "invoice", org_a.id)
    register_portal_token("tok", None, "invoice", org_a.id)
    assert PortalAccessToken.objects.count() == 0
