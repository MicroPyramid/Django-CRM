"""Macro model tests — primarily the scope/owner consistency constraint."""

import pytest
from django.db import IntegrityError, transaction

from macros.models import Macro


class TestMacroScopeConstraint:
    def test_org_scope_with_owner_rejected(self, org_a, user_profile):
        with pytest.raises(IntegrityError), transaction.atomic():
            Macro.objects.create(
                org=org_a,
                title="bad",
                body="x",
                scope=Macro.SCOPE_ORG,
                owner=user_profile,
            )

    def test_personal_scope_without_owner_rejected(self, org_a):
        with pytest.raises(IntegrityError), transaction.atomic():
            Macro.objects.create(
                org=org_a,
                title="bad",
                body="x",
                scope=Macro.SCOPE_PERSONAL,
                owner=None,
            )

    def test_org_scope_without_owner_allowed(self, org_a):
        m = Macro.objects.create(
            org=org_a, title="ok", body="x", scope=Macro.SCOPE_ORG
        )
        assert m.id is not None
        assert m.owner is None

    def test_personal_scope_with_owner_allowed(self, org_a, user_profile):
        m = Macro.objects.create(
            org=org_a,
            title="ok",
            body="x",
            scope=Macro.SCOPE_PERSONAL,
            owner=user_profile,
        )
        assert m.id is not None
        assert m.owner_id == user_profile.id

    def test_default_is_active_true_and_usage_zero(self, org_a):
        m = Macro.objects.create(
            org=org_a, title="t", body="b", scope=Macro.SCOPE_ORG
        )
        assert m.is_active is True
        assert m.usage_count == 0

    def test_str_repr(self, org_a):
        m = Macro.objects.create(
            org=org_a, title="Greeting", body="x", scope=Macro.SCOPE_ORG
        )
        assert str(m) == "Greeting (org)"
