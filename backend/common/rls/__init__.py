"""
Row-Level Security (RLS) Configuration for PostgreSQL.

This module provides centralized configuration and SQL generators for
database-level multi-tenancy using PostgreSQL Row-Level Security.

RLS ensures that:
1. Queries automatically filter by current org
2. Even if application code misses a filter, data is protected
3. Direct SQL access respects org boundaries

Usage:
    from common.rls import RLS_CONFIG, get_enable_policy_sql

    # Enable RLS on a table
    cursor.execute(get_enable_policy_sql('lead'))

    # Check config
    tables = RLS_CONFIG['tables']
"""

# PostgreSQL session variable for org context
# Set via: SELECT set_config('app.current_org', '<org_id>', true)
CONTEXT_VARIABLE = "app.current_org"

# Policy names
ISOLATION_POLICY = "org_isolation"
INSERT_POLICY = "org_insert_check"

# All org-scoped tables that need RLS policies
# Add new org-scoped tables here
# NOTE: Only include tables that have an org_id column directly
# Table names must match actual PostgreSQL table names (check via \dt)
ORG_SCOPED_TABLES = [
    # Core business entities
    "lead",
    "accounts",  # Note: plural
    "contacts",  # Note: plural
    "opportunity",
    "case",  # Note: singular
    "task",
    "invoice",
    # Supporting entities
    "comment",
    "commentFiles",  # Security fix: Added for RLS protection
    "attachments",
    "document",
    "teams",
    "activity",
    "tags",
    "address",
    "solution",
    # Boards (Kanban)
    "board",
    "board_column",
    "board_task",
    "board_member",
    # Settings
    "apiSettings",  # Note: camelCase
    # Email & Invoicing
    "account_email",
    "emailLogs",
    "invoice_history",
    "invoice_line_item",
    "invoice_template",
    "payment",
    "estimate",
    "estimate_line_item",
    "recurring_invoice",
    "recurring_invoice_line_item",
    # Products
    "product",
    # Security & Audit
    "security_audit_log",
]

# Centralized RLS configuration
RLS_CONFIG = {
    "context_variable": CONTEXT_VARIABLE,
    "tables": ORG_SCOPED_TABLES,
    "policies": {
        "isolation": ISOLATION_POLICY,
        "insert": INSERT_POLICY,
    },
}


def get_check_table_exists_sql():
    """
    Returns SQL to check if a table exists.

    Usage:
        cursor.execute(get_check_table_exists_sql(), [table_name])
        exists = cursor.fetchone()[0]
    """
    return """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = %s
        )
    """


def get_check_rls_status_sql():
    """
    Returns SQL to check RLS status for a table.

    Usage:
        cursor.execute(get_check_rls_status_sql(), [table_name])
        rls_enabled, rls_forced = cursor.fetchone()
    """
    return """
        SELECT relrowsecurity, relforcerowsecurity
        FROM pg_class
        WHERE relname = %s AND relnamespace = 'public'::regnamespace
    """


def get_set_context_sql():
    """
    Returns SQL to set the org context.

    Uses set_config with is_local=false to persist for the SESSION,
    not just the current transaction. This is required because Django
    uses autocommit mode by default.

    The middleware must reset this after each request to prevent leakage.

    Usage:
        cursor.execute(get_set_context_sql(), [org_id])
    """
    return f"SELECT set_config('{CONTEXT_VARIABLE}', %s, false)"


def get_enable_policy_sql(table):
    """
    Returns SQL to enable RLS on a table with proper policies.

    This creates:
    1. Enables RLS on the table
    2. Forces RLS for table owner
    3. Creates isolation policy for SELECT/UPDATE/DELETE
    4. Creates insert check policy

    Args:
        table: Table name

    Returns:
        SQL string to execute
    """
    return f"""
        -- Enable RLS on table
        ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY;
        ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY;

        -- Drop existing policies if any
        DROP POLICY IF EXISTS {ISOLATION_POLICY} ON "{table}";
        DROP POLICY IF EXISTS {INSERT_POLICY} ON "{table}";

        -- Create isolation policy (SELECT, UPDATE, DELETE)
        -- Uses NULLIF to return no rows when context is not set (fail-safe)
        CREATE POLICY {ISOLATION_POLICY} ON "{table}"
            FOR ALL
            USING (
                org_id::text = NULLIF(current_setting('{CONTEXT_VARIABLE}', true), '')
            );

        -- Create insert check policy
        CREATE POLICY {INSERT_POLICY} ON "{table}"
            FOR INSERT
            WITH CHECK (
                org_id::text = NULLIF(current_setting('{CONTEXT_VARIABLE}', true), '')
            );
    """


def get_disable_policy_sql(table):
    """
    Returns SQL to disable RLS on a table.

    Args:
        table: Table name

    Returns:
        SQL string to execute
    """
    return f"""
        -- Drop policies
        DROP POLICY IF EXISTS {ISOLATION_POLICY} ON "{table}";
        DROP POLICY IF EXISTS {INSERT_POLICY} ON "{table}";

        -- Disable RLS
        ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY;
    """
