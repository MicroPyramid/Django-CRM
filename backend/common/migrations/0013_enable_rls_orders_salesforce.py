# Enable RLS on orders tables
# Note: salesforce_imports tables were moved to enterprise edition

from django.db import migrations

from common.rls import (
    get_check_table_exists_sql,
    get_disable_policy_sql,
    get_enable_policy_sql,
)

TABLES = [
    "orders",
    "order_line_item",
]


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
    """Enable RLS on orders tables."""
    if schema_editor.connection.vendor != "postgresql":
        print("RLS is only supported on PostgreSQL. Skipping.")
        return

    with schema_editor.connection.cursor() as cursor:
        for table in TABLES:
            # Check if table exists
            cursor.execute(get_check_table_exists_sql(), [table])
            if not cursor.fetchone()[0]:
                print(f"  Skipping {table} (table does not exist)")
                continue

            # Check if org_id column exists
            if not check_column_exists(cursor, table, "org_id"):
                print(f"  Skipping {table} (no org_id column)")
                continue

            # Enable RLS
            cursor.execute(get_enable_policy_sql(table))
            print(f"  Enabled RLS on {table}")


def disable_rls(apps, schema_editor):
    """Disable RLS on orders tables (rollback)."""
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        for table in TABLES:
            cursor.execute(get_check_table_exists_sql(), [table])
            if not cursor.fetchone()[0]:
                continue

            if not check_column_exists(cursor, table, "org_id"):
                continue

            cursor.execute(get_disable_policy_sql(table))
            print(f"  Disabled RLS on {table}")


class Migration(migrations.Migration):
    """
    Enable Row-Level Security (RLS) on orders tables.
    """

    dependencies = [
        ("common", "0012_add_tag_color_description_isactive"),
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(enable_rls, disable_rls),
    ]
