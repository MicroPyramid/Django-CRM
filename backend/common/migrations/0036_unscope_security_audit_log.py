# Drop the Row-Level Security policies from `security_audit_log`.
#
# The table was registered in ORG_SCOPED_TABLES, so `common/0028` stamped it
# with the standard pair: an isolation policy for SELECT/UPDATE/DELETE and an
# insert check, both comparing `org_id::text` to `app.current_org`.
#
# `SecurityAuditLog.org` is `null=True` on purpose. The events the table exists
# to record are the ones that happen with no org in hand: LOGIN_FAILURE,
# API_KEY_INVALID, PERMISSION_DENIED, TOKEN_REVOKED, and CROSS_ORG_ATTEMPT,
# which by definition straddles two tenants. `NULL = anything` evaluates to
# NULL rather than true, so the insert check refused every one of those rows on
# any connection that RLS actually binds, which is what RLS_SETUP.md requires of
# a production database. `AuditLogger._log` wraps the write in
# `except Exception: logger.error(...)`, so nothing surfaced: the security audit
# trail was simply empty in correctly configured deployments, for precisely the
# hostile events it was built to capture.
#
# It stayed hidden because the development database user is a superuser, which
# bypasses RLS outright, and CI ran on SQLite, which has no RLS at all. A
# PostgreSQL CI job running as a NOSUPERUSER NOBYPASSRLS role is what surfaced
# it, with 175 refusals in one run.
#
# Per-tenant isolation is the wrong control for this table rather than a control
# that needs adjusting: it holds one org-spanning record of authentication and
# authorization events. Nothing in the application reads it (`SecurityAuditLog`
# is imported by `common/models.py` only to re-export the name, and by one
# test), so removing the policies exposes nothing through any endpoint.
# `common/tests/test_audit_log_not_exposed.py` is the guard that keeps that
# true, because once the policies are gone an endpoint serving these rows would
# have no safety net beneath a missing org filter.
#
# atomic = False, matching common/0028 and common/0034: DROP POLICY and ALTER
# TABLE each take an ACCESS EXCLUSIVE lock, so committing per statement keeps
# each lock brief.

from django.db import migrations

from common.rls import (
    get_check_table_exists_sql,
    get_disable_policy_sql,
    get_enable_policy_sql,
)

TABLE = "security_audit_log"


def unscope_audit_log(apps, schema_editor):
    """Drop the isolation and insert-check policies, and disable RLS."""
    if schema_editor.connection.vendor != "postgresql":
        print("RLS is only supported on PostgreSQL. Skipping.")
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(get_check_table_exists_sql(), [TABLE])
        if not cursor.fetchone()[0]:
            print(f"  Skipping {TABLE} (table does not exist)")
            return

        cursor.execute(get_disable_policy_sql(TABLE))
        print(f"  Dropped RLS policies on {TABLE}")


def restamp_audit_log(apps, schema_editor):
    """Put the policies back, so the migration is genuinely reversible.

    Reversing restores the broken behaviour described above. That is correct
    for a reverse migration: it returns the database to the state the previous
    code revision expects, and the previous revision is the one whose audit
    writes fail.
    """
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(get_check_table_exists_sql(), [TABLE])
        if not cursor.fetchone()[0]:
            return
        cursor.execute(get_enable_policy_sql(TABLE))


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("common", "0035_sync_is_organization_admin_with_role"),
    ]

    operations = [
        migrations.RunPython(unscope_audit_log, restamp_audit_log),
    ]
