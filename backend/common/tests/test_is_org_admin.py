"""``common.permissions.is_org_admin``: both directions, and no second copy.

This rule existed as ten private functions across the backend, in three
spellings, and CLAUDE.md is explicit that a permission check has to be proven
able to return both ``True`` and ``False``. A check that can only answer one
way is dead either as a gate or as a grant, and nothing about reading it says
which.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from common.permissions import IsOrgAdmin, is_org_admin


class _FakeProfile:
    """Only the two attributes the rule reads.

    A real ``Profile`` needs an org and a user, and nothing here is about the
    database. ``is_admin`` is deliberately absent: the rule reads
    ``is_organization_admin``, which is the column, and the property that
    aliases it is what half the old copies used instead.
    """

    def __init__(self, role="USER", is_organization_admin=False):
        self.role = role
        self.is_organization_admin = is_organization_admin


class TestBothDirections:
    def test_an_admin_by_role_is_an_admin(self):
        assert is_org_admin(_FakeProfile(role="ADMIN")) is True

    def test_an_admin_by_flag_is_an_admin(self):
        assert is_org_admin(_FakeProfile(is_organization_admin=True)) is True

    def test_a_plain_member_is_not(self):
        assert is_org_admin(_FakeProfile()) is False

    def test_a_missing_profile_is_not(self):
        """Five of the ten copies raised ``AttributeError`` here.

        A view with no org context has no profile, so this is not theoretical:
        it decided whether the caller got a clean 403 or a 500.
        """
        assert is_org_admin(None) is False

    def test_an_object_without_the_flag_is_judged_on_role_alone(self):
        """Not every caller passes a full ``Profile``.

        ``getattr`` with a default keeps that a ``False`` rather than an
        ``AttributeError``, which is the behaviour the two None-safe copies had
        and the other eight did not.
        """

        class RoleOnly:
            role = "USER"

        assert is_org_admin(RoleOnly()) is False
        RoleOnly.role = "ADMIN"
        assert is_org_admin(RoleOnly()) is True


class TestThePermissionClassUsesTheSameRule:
    """``IsOrgAdmin`` used to spell the rule out a second time in its body."""

    class _Request:
        def __init__(self, profile):
            self.profile = profile

    def test_admin_allowed(self):
        request = self._Request(_FakeProfile(role="ADMIN"))
        assert IsOrgAdmin().has_permission(request, view=None) is True

    def test_member_refused(self):
        request = self._Request(_FakeProfile())
        assert IsOrgAdmin().has_permission(request, view=None) is False

    def test_request_with_no_profile_attribute_refused(self):
        assert IsOrgAdmin().has_permission(object(), view=None) is False


def _backend_root():
    return Path(__file__).resolve().parents[2]


def test_no_module_defines_its_own_admin_check():
    """Guard the consolidation with the source, not with a comment.

    The ten copies did not appear at once; each was written by somebody who
    needed the rule in a new module and had no reason to know it already
    existed eight times. This fails the moment an eleventh is added, which is
    the only thing that keeps them from coming back.
    """
    offenders = []
    for path in _backend_root().rglob("*.py"):
        parts = path.parts
        if any(p in {".venv", "venv", "migrations", "node_modules"} for p in parts):
            continue
        if path.name == Path(__file__).name:
            continue
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:  # pragma: no cover - nothing in the tree should hit this
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                node.name in {"_is_admin", "is_admin_profile", "_is_org_admin"}
            ):
                offenders.append(f"{path.relative_to(_backend_root())}:{node.lineno}")

    assert offenders == [], (
        "These modules define their own admin check again; import "
        "`is_org_admin` from `common.permissions` instead: " + ", ".join(offenders)
    )


@pytest.mark.django_db
def test_a_real_profile_agrees_with_the_fake_one(admin_profile, user_profile):
    """The fakes above are only worth anything if the real model matches them."""
    assert is_org_admin(admin_profile) is True
    assert is_org_admin(user_profile) is False

    user_profile.is_organization_admin = True
    assert is_org_admin(user_profile) is True
