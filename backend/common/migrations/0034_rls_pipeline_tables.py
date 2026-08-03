# Stamp Row-Level Security (RLS) policies on the Kanban pipeline and stage
# tables.
#
# lead_pipeline, lead_stage, case_pipeline, case_stage, task_pipeline and
# task_stage all carry org_id directly, but they were absent from
# ORG_SCOPED_TABLES and no migration ever created their policies. The apps that
# created the tables (leads/0012, cases/0009, tasks/0009) contain no RLS SQL,
# and common/0028 only iterates RLS_CONFIG["tables"], which did not list them.
#
# Deployed databases had the policies from an out-of-band step, so the gap was
# invisible there. A database built purely from migrations: CI, and any fresh
# deploy, got none, leaving these tables with no safety net beneath the ORM's
# org filters. Vertical packs write to all six on every apply, which is what
# made the gap load-bearing rather than theoretical.
#
# The explicit cross-app dependencies below matter: without them Django is free
# to run this before the tables exist, the existence guard would skip every one,
# and a fresh database would again end up with no policies.
#
# Idempotent: the generated SQL opens with DROP POLICY IF EXISTS, so re-running
# is safe. On databases carrying the out-of-band policies this also restamps
# them into the InitPlan form common/0028 introduced.
#
# atomic = False, matching common/0028: DROP/CREATE POLICY each take an ACCESS
# EXCLUSIVE lock, so committing per statement keeps each lock brief.
#
# RLS Configuration: See common/rls/__init__.py for centralized policy definitions

from django.db import migrations

from common.rls import get_check_table_exists_sql, get_enable_policy_sql

PIPELINE_TABLES = [
    "lead_pipeline",
    "lead_stage",
    "case_pipeline",
    "case_stage",
    "task_pipeline",
    "task_stage",
]


def stamp_pipeline_rls(apps, schema_editor):
    """Create the isolation and insert-check policies on the pipeline tables."""
    if schema_editor.connection.vendor != "postgresql":
        print("RLS is only supported on PostgreSQL. Skipping.")
        return

    stamped = 0

    with schema_editor.connection.cursor() as cursor:
        for table in PIPELINE_TABLES:
            cursor.execute(get_check_table_exists_sql(), [table])
            if not cursor.fetchone()[0]:
                print(f"  Skipping {table} (table does not exist)")
                continue

            cursor.execute(get_enable_policy_sql(table))
            stamped += 1

    print(f"  Stamped RLS policies on {stamped} pipeline table(s)")


def noop_reverse(apps, schema_editor):
    """
    No-op.

    Rolling back would mean dropping tenant-isolation policies, which is never
    the safe direction. The policies are value-preserving for correctly scoped
    queries, so leaving them in place breaks nothing on an older code revision.
    """


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("common", "0033_alter_securityauditlog_event_type"),
        ("leads", "0012_lead_kanban_pipeline"),
        ("cases", "0009_case_kanban"),
        ("tasks", "0009_task_kanban"),
    ]

    operations = [
        migrations.RunPython(stamp_pipeline_rls, noop_reverse),
    ]
