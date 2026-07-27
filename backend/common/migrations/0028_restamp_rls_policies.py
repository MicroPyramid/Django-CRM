# Re-stamp Row-Level Security (RLS) policies on all org-scoped tables.
#
# The policy SQL in common/rls/__init__.py now wraps the session read in a
# scalar sub-select so Postgres hoists it to a one-time InitPlan instead of
# re-evaluating current_setting() once per row scanned:
#
#     org_id::text = (select NULLIF(current_setting('app.current_org', true), ''))
#
# get_enable_policy_sql() is only ever called from migrations, and those have
# already been applied on existing databases, so the new SQL would otherwise
# reach fresh installs only. This migration re-runs the codegen over every
# org-scoped table so deployed databases pick it up too.
#
# The re-stamp is value-preserving: the predicate returns the same rows before
# and after (unset context -> NULLIF -> NULL -> no rows, same fail-safe), so
# this is a planner optimization, not a change to tenant isolation.
#
# atomic = False: DROP/CREATE POLICY each take an ACCESS EXCLUSIVE lock on the
# table. Committing per statement keeps each lock brief instead of holding all
# of them until the end of one long transaction. The operation is idempotent
# (the generated SQL opens with DROP POLICY IF EXISTS), so a run that fails
# part-way can simply be re-run.
#
# RLS Configuration: See common/rls/__init__.py for centralized policy definitions

from django.db import migrations

from common.rls import (
    RLS_CONFIG,
    get_check_table_exists_sql,
    get_enable_policy_sql,
)


def check_column_exists(cursor, table, column):
    """Check if a column exists in a table."""
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
            AND column_name = %s
        )
    """,
        [table, column],
    )
    return cursor.fetchone()[0]


def restamp_rls_policies(apps, schema_editor):
    """Re-create the isolation and insert-check policies on every org-scoped table."""
    if schema_editor.connection.vendor != "postgresql":
        print("RLS is only supported on PostgreSQL. Skipping.")
        return

    restamped = 0

    with schema_editor.connection.cursor() as cursor:
        for table in RLS_CONFIG["tables"]:
            # Tables belonging to apps whose migrations have not run yet are
            # skipped; those apps stamp their own policies with the current
            # codegen, so they already get the new SQL.
            cursor.execute(get_check_table_exists_sql(), [table])
            if not cursor.fetchone()[0]:
                print(f"  Skipping {table} (table does not exist)")
                continue

            if not check_column_exists(cursor, table, "org_id"):
                print(f"  Skipping {table} (no org_id column)")
                continue

            # Unconditional: no pg_policies existence guard. The whole point is
            # to replace policies that already exist with the InitPlan form.
            cursor.execute(get_enable_policy_sql(table))
            restamped += 1

    print(f"  Re-stamped RLS policies on {restamped} table(s)")


def noop_reverse(apps, schema_editor):
    """
    No-op.

    Rolling back leaves the InitPlan-form policies in place. They are
    functionally identical to the previous form, so there is nothing unsafe to
    undo, and regenerating the old SQL would mean duplicating the superseded
    codegen here purely to write it back.
    """


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("common", "0027_personalaccesstoken"),
    ]

    operations = [
        migrations.RunPython(restamp_rls_policies, noop_reverse),
    ]
