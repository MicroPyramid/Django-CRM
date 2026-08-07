"""RLS coverage for the Kanban pipeline and stage tables.

These six tables carry org_id directly but were absent from ORG_SCOPED_TABLES,
and neither leads/0012, cases/0009 nor tasks/0009 stamped a policy. Deployed
databases had the policies from an out-of-band step, so the gap only existed on
databases built purely from migrations, CI, and any fresh deploy.

The pytest database is built by running migrations and nothing else, which is
precisely the environment that was broken. common/0034 closes it; these tests
keep it closed.
"""

import pytest
from django.db import connection

from common.rls import ORG_SCOPED_TABLES

PIPELINE_TABLES = [
    "lead_pipeline",
    "lead_stage",
    "case_pipeline",
    "case_stage",
    "task_pipeline",
    "task_stage",
]


def test_pipeline_tables_are_registered_as_org_scoped():
    """Registration is what makes the central tooling (manage_rls --status,
    common/0028's re-stamp) able to see these tables at all."""
    missing = [t for t in PIPELINE_TABLES if t not in ORG_SCOPED_TABLES]
    assert not missing, f"tables missing from ORG_SCOPED_TABLES: {missing}"


@pytest.mark.postgres_only
@pytest.mark.django_db
def test_pipeline_tables_have_rls_policies():
    """Every pipeline table has RLS enabled with both policies, from migrations
    alone. Verified to fail without common/0034."""
    if connection.vendor != "postgresql":
        pytest.skip("RLS requires PostgreSQL")

    broken = []
    with connection.cursor() as cur:
        for table in PIPELINE_TABLES:
            cur.execute(
                """
                SELECT c.relrowsecurity,
                       (SELECT COUNT(*) FROM pg_policy p WHERE p.polrelid = c.oid)
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = %s
                """,
                [table],
            )
            row = cur.fetchone()
            if row is None:
                broken.append((table, "table does not exist"))
            elif not row[0]:
                broken.append((table, "RLS not enabled"))
            elif row[1] < 2:
                broken.append((table, f"expected 2 policies, found {row[1]}"))

    assert not broken, f"pipeline tables without RLS: {broken}"


@pytest.mark.postgres_only
@pytest.mark.django_db
def test_pipeline_policies_use_the_org_context_variable():
    """The isolation policy must key on app.current_org, not something else."""
    if connection.vendor != "postgresql":
        pytest.skip("RLS requires PostgreSQL")

    with connection.cursor() as cur:
        for table in PIPELINE_TABLES:
            cur.execute(
                """
                SELECT pg_get_expr(p.polqual, p.polrelid)
                FROM pg_policy p
                JOIN pg_class c ON c.oid = p.polrelid
                WHERE c.relname = %s AND p.polname = 'org_isolation'
                """,
                [table],
            )
            row = cur.fetchone()
            assert row is not None, f"{table} has no org_isolation policy"
            assert "app.current_org" in row[0], (
                f"{table}: unexpected predicate {row[0]}"
            )
            assert "org_id" in row[0], f"{table}: predicate does not filter org_id"
