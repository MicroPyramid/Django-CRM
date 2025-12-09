# Enable RLS on new invoice-related tables

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


# New invoice-related tables that need RLS
NEW_TABLES = [
    "invoice_template",
    "payment",
    "estimate",
    "estimate_line_item",
    "recurring_invoice",
    "recurring_invoice_line_item",
]


def enable_rls(apps, schema_editor):
    """Enable RLS on new invoice-related tables."""
    if schema_editor.connection.vendor != "postgresql":
        print("RLS is only supported on PostgreSQL. Skipping.")
        return

    with schema_editor.connection.cursor() as cursor:
        for table in NEW_TABLES:
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
    """Disable RLS on new invoice-related tables (rollback)."""
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        for table in NEW_TABLES:
            cursor.execute(get_check_table_exists_sql(), [table])
            if not cursor.fetchone()[0]:
                continue

            if not check_column_exists(cursor, table, "org_id"):
                continue

            cursor.execute(get_disable_policy_sql(table))
            print(f"  Disabled RLS on {table}")


class Migration(migrations.Migration):
    """
    Enable Row-Level Security (RLS) on new invoice-related tables:
    - invoice_template
    - payment
    - estimate
    - estimate_line_item
    - recurring_invoice
    - recurring_invoice_line_item
    """

    dependencies = [
        ("common", "0009_add_org_company_profile"),
        ("invoices", "0004_estimate_estimatelineitem_invoicetemplate_payment_and_more"),
    ]

    operations = [
        migrations.RunPython(enable_rls, disable_rls),
    ]
