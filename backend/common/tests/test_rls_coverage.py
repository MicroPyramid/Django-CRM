import pytest
from django.db import connection

from common.testing import (
    TABLES_WITHOUT_RLS,
    org_tables_not_covered,
    rls_policy_gaps,
)


def test_every_org_table_is_listed_or_excluded():
    assert org_tables_not_covered() == []


def test_the_listing_check_can_fail():
    unlisted = org_tables_not_covered(excluded={})
    assert {p.split(":")[0] for p in unlisted} == set(TABLES_WITHOUT_RLS)
    assert any(
        p.startswith("no_such_table:")
        for p in org_tables_not_covered({**TABLES_WITHOUT_RLS, "no_such_table": "x"})
    )
    assert any(
        p.startswith("lead:")
        for p in org_tables_not_covered({**TABLES_WITHOUT_RLS, "lead": "x"})
    )


@pytest.mark.postgres_only
def test_every_listed_table_has_its_policies():
    if connection.vendor != "postgresql":
        pytest.skip("RLS requires PostgreSQL")
    assert rls_policy_gaps() == []


@pytest.mark.postgres_only
def test_the_policy_check_can_fail():
    if connection.vendor != "postgresql":
        pytest.skip("RLS requires PostgreSQL")
    gaps = rls_policy_gaps(["security_audit_log", "no_such_table"])
    assert any(p.startswith("security_audit_log:") for p in gaps)
    assert any(p.startswith("no_such_table:") for p in gaps)
