# Enable RLS on opportunity_line_item table

from django.db import migrations

from common.rls import (
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
    """Enable RLS on opportunity_line_item table."""
    if schema_editor.connection.vendor != "postgresql":
        print("RLS is only supported on PostgreSQL. Skipping.")
        return

    table = "opportunity_line_item"

    with schema_editor.connection.cursor() as cursor:
        # Check if table exists
        cursor.execute(get_check_table_exists_sql(), [table])
        if not cursor.fetchone()[0]:
            print(f"  Skipping {table} (table does not exist)")
            return

        # Check if org_id column exists
        if not check_column_exists(cursor, table, "org_id"):
            print(f"  Skipping {table} (no org_id column)")
            return

        # Enable RLS
        cursor.execute(get_enable_policy_sql(table))
        print(f"  Enabled RLS on {table}")


def disable_rls(apps, schema_editor):
    """Disable RLS on opportunity_line_item table (rollback)."""
    if schema_editor.connection.vendor != "postgresql":
        return

    table = "opportunity_line_item"

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(get_check_table_exists_sql(), [table])
        if not cursor.fetchone()[0]:
            return

        if not check_column_exists(cursor, table, "org_id"):
            return

        cursor.execute(get_disable_policy_sql(table))
        print(f"  Disabled RLS on {table}")


class Migration(migrations.Migration):
    """
    Enable Row-Level Security (RLS) on opportunity_line_item table.
    """

    dependencies = [
        ("common", "0010_enable_rls_invoice_models"),
        ("opportunity", "0006_add_opportunity_line_item"),
    ]

    operations = [
        migrations.RunPython(enable_rls, disable_rls),
    ]
