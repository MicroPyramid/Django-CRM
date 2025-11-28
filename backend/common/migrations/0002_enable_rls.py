# Row-Level Security (RLS) Migration
# Enables PostgreSQL RLS on all org-scoped tables for multi-tenant isolation
#
# RLS Configuration: See common/rls/__init__.py for centralized policy definitions

from django.db import migrations

from common.rls import (
    RLS_CONFIG,
    get_check_table_exists_sql,
    get_disable_policy_sql,
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


def enable_rls(apps, schema_editor):
    """Enable RLS on all org-scoped tables."""
    if schema_editor.connection.vendor != "postgresql":
        print("RLS is only supported on PostgreSQL. Skipping.")
        return

    isolation_policy = RLS_CONFIG["policies"]["isolation"]

    with schema_editor.connection.cursor() as cursor:
        for table in RLS_CONFIG["tables"]:
            # Check if table exists
            cursor.execute(get_check_table_exists_sql(), [table])
            if not cursor.fetchone()[0]:
                print(f"  Skipping {table} (table does not exist)")
                continue

            # Check if org_id column exists
            if not check_column_exists(cursor, table, "org_id"):
                print(f"  Skipping {table} (no org_id column)")
                continue

            # Check if policy already exists
            cursor.execute(
                """
                SELECT COUNT(*) FROM pg_policies
                WHERE tablename = %s AND policyname = %s
            """,
                [table, isolation_policy],
            )

            if cursor.fetchone()[0] == 0:
                cursor.execute(get_enable_policy_sql(table))
                print(f"  Enabled RLS on {table}")
            else:
                print(f"  RLS already enabled on {table}")


def disable_rls(apps, schema_editor):
    """Disable RLS on all org-scoped tables (rollback)."""
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        for table in RLS_CONFIG["tables"]:
            cursor.execute(get_check_table_exists_sql(), [table])
            if not cursor.fetchone()[0]:
                continue

            if not check_column_exists(cursor, table, "org_id"):
                continue

            cursor.execute(get_disable_policy_sql(table))
            print(f"  Disabled RLS on {table}")


class Migration(migrations.Migration):
    """
    Enable Row-Level Security (RLS) on all organization-scoped tables.

    This provides database-level isolation ensuring that:
    1. Queries automatically filter by current org
    2. Even if application code misses a filter, data is protected
    3. Direct SQL access respects org boundaries

    Prerequisites:
    - PostgreSQL 9.5+
    - Database user must NOT be a superuser (superusers bypass RLS)
    - Application must set app.current_org before queries

    Configuration:
    - Table list and policy SQL are defined in common/rls/__init__.py
    - Use `python manage.py manage_rls --status` to check RLS status
    """

    dependencies = [
        ("common", "0001_initial"),
        ("accounts", "0002_initial"),
        ("cases", "0002_initial"),
        ("contacts", "0001_initial"),
        ("invoices", "0001_initial"),
        ("leads", "0001_initial"),
        ("opportunity", "0001_initial"),
        ("tasks", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(enable_rls, disable_rls),
    ]
