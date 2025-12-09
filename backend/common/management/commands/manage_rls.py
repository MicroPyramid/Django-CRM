"""
Management command to check Row-Level Security (RLS) status.

Usage:
    python manage.py manage_rls --status          # Check RLS status
    python manage.py manage_rls --test            # Test RLS is working
    python manage.py manage_rls --verify-user     # Verify DB user is not superuser

RLS Configuration: See common/rls/__init__.py for centralized policy definitions.
RLS is enabled/disabled via Django migrations, not this command.
"""

from django.core.management.base import BaseCommand
from django.db import connection

from common.rls import RLS_CONFIG, get_check_rls_status_sql, get_set_context_sql


class Command(BaseCommand):
    help = "Check Row-Level Security (RLS) status for multi-tenancy"

    # Use centralized RLS configuration
    ORG_SCOPED_TABLES = RLS_CONFIG["tables"]

    def add_arguments(self, parser):
        parser.add_argument(
            "--status", action="store_true", help="Check RLS status for all tables"
        )
        parser.add_argument(
            "--test", action="store_true", help="Test that RLS is working correctly"
        )
        parser.add_argument(
            "--verify-user",
            action="store_true",
            help="Verify database user is not a superuser",
        )

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            self.stderr.write(self.style.ERROR("RLS is only supported on PostgreSQL"))
            return

        if options["status"]:
            self.check_status()
        elif options["test"]:
            self.test_rls()
        elif options["verify_user"]:
            self.verify_user()
        else:
            self.check_status()

    def check_status(self):
        """Check RLS status for all org-scoped tables."""
        self.stdout.write(self.style.MIGRATE_HEADING("RLS Status:"))
        self.stdout.write("")

        with connection.cursor() as cursor:
            # Check if current user is superuser
            cursor.execute(
                "SELECT current_user, usesuper FROM pg_user WHERE usename = current_user"
            )
            user, is_super = cursor.fetchone()

            if is_super:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Database user "{user}" is a SUPERUSER - RLS will be bypassed!'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  Database user "{user}" is not a superuser - RLS will be enforced'
                    )
                )

            self.stdout.write("")

            enabled_count = 0
            disabled_count = 0

            for table in self.ORG_SCOPED_TABLES:
                cursor.execute(get_check_rls_status_sql(), [table])

                result = cursor.fetchone()
                if result:
                    rls_enabled, rls_forced = result
                    if rls_enabled:
                        status = self.style.SUCCESS("ENABLED")
                        if rls_forced:
                            status += " (forced)"
                        enabled_count += 1
                    else:
                        status = self.style.WARNING("disabled")
                        disabled_count += 1
                else:
                    status = self.style.ERROR("TABLE NOT FOUND")

                self.stdout.write(f"  {table}: {status}")

            self.stdout.write("")
            self.stdout.write(f"  Enabled: {enabled_count}, Disabled: {disabled_count}")

    def test_rls(self):
        """Test that RLS is working correctly."""
        self.stdout.write(self.style.MIGRATE_HEADING("Testing RLS..."))

        set_context_sql = get_set_context_sql()

        with connection.cursor() as cursor:
            # Find orgs that have leads (need to check each org since RLS is active)
            cursor.execute(
                "SELECT id FROM organization ORDER BY created_at DESC LIMIT 50"
            )
            all_orgs = cursor.fetchall()

            orgs_with_leads = []
            for (org_id,) in all_orgs:
                cursor.execute(set_context_sql, [str(org_id)])
                cursor.execute("SELECT COUNT(*) FROM lead")
                if cursor.fetchone()[0] > 0:
                    orgs_with_leads.append(str(org_id))
                    if len(orgs_with_leads) >= 2:
                        break

            if len(orgs_with_leads) < 1:
                # Fall back to first 2 orgs for testing
                cursor.execute("SELECT id FROM organization LIMIT 2")
                orgs = cursor.fetchall()
                if len(orgs) < 2:
                    self.stdout.write(
                        self.style.WARNING(
                            "Need at least 2 orgs to test RLS. Skipping."
                        )
                    )
                    return
                org_a = str(orgs[0][0])
                org_b = str(orgs[1][0])
            else:
                org_a = orgs_with_leads[0]
                org_b = (
                    orgs_with_leads[1]
                    if len(orgs_with_leads) > 1
                    else str(all_orgs[0][0])
                )

            # Test with org_a context
            cursor.execute(set_context_sql, [org_a])
            cursor.execute("SELECT COUNT(*) FROM lead")
            count_a = cursor.fetchone()[0]

            # Test with org_b context
            cursor.execute(set_context_sql, [org_b])
            cursor.execute("SELECT COUNT(*) FROM lead")
            count_b = cursor.fetchone()[0]

            # Test with no context
            cursor.execute(set_context_sql, [""])
            cursor.execute("SELECT COUNT(*) FROM lead")
            count_none = cursor.fetchone()[0]

            self.stdout.write(f"  Leads with org_a context: {count_a}")
            self.stdout.write(f"  Leads with org_b context: {count_b}")
            self.stdout.write(f"  Leads with no context: {count_none}")

            if count_a == 0 and count_b == 0 and count_none == 0:
                self.stdout.write(
                    self.style.WARNING(
                        "No lead data found. Create leads for different orgs to test RLS isolation."
                    )
                )
            elif count_none == 0 and (count_a > 0 or count_b > 0):
                self.stdout.write(
                    self.style.SUCCESS("RLS is working - no data without context")
                )
            elif count_none > 0:
                self.stdout.write(
                    self.style.WARNING(
                        "RLS may not be fully enabled - data visible without context. "
                        "This is expected if the policy allows empty context."
                    )
                )

    def verify_user(self):
        """Verify the database user is not a superuser."""
        self.stdout.write(self.style.MIGRATE_HEADING("Verifying database user..."))

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT usename, usesuper, usecreatedb
                FROM pg_user
                WHERE usename = current_user
            """
            )
            user, is_super, can_create_db = cursor.fetchone()

            self.stdout.write(f"  Current user: {user}")
            self.stdout.write(f"  Is superuser: {is_super}")
            self.stdout.write(f"  Can create DB: {can_create_db}")

            if is_super:
                self.stdout.write("")
                self.stdout.write(
                    self.style.ERROR(
                        "WARNING: Superusers bypass RLS!\n"
                        "Create a non-superuser for the application:\n\n"
                        "  CREATE USER crm_app WITH PASSWORD 'secure_password';\n"
                        "  GRANT CONNECT ON DATABASE bottlecrm TO crm_app;\n"
                        "  GRANT USAGE ON SCHEMA public TO crm_app;\n"
                        "  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO crm_app;\n"
                        "  GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO crm_app;\n"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("Database user is properly configured for RLS")
                )
