"""
Django management command to migrate data from Prisma/PostgreSQL to Django.

Usage:
    python manage.py migrate_from_prisma --db-host=<host> --db-name=<name> --db-user=<user> --db-password=<pass>

    Options:
        --dry-run: Validate data without inserting
        --batch-size: Number of records per batch (default: 1000)
        --skip-existing: Skip records that already exist
        --only: Comma-separated list of models to migrate (e.g., "User,Account,Contact")
"""

import logging
import uuid
from datetime import datetime
from decimal import Decimal

import psycopg2
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone
from psycopg2.extras import RealDictCursor

from accounts.models import Account
from cases.models import Case, Solution

# Import Django models
from common.models import (
    Activity,
    Address,
    Attachments,
    Comment,
    CommentFiles,
    ContactFormSubmission,
    Document,
    Org,
    Profile,
    SessionToken,
    Tags,
    Teams,
    User,
)
from contacts.models import Contact
from invoices.models import Invoice, Product
from leads.models import Company, Lead
from opportunity.models import Opportunity
from tasks.models import Board, BoardColumn, BoardMember, BoardTask, Task

logger = logging.getLogger(__name__)


LEAD_STATUS_MAP = {
    "NEW": "assigned",
    "PENDING": "assigned",
    "CONTACTED": "in process",
    "QUALIFIED": "converted",
    "UNQUALIFIED": "recycled",
    "CONVERTED": "closed",
}

LEAD_SOURCE_MAP = {
    "WEB": "email",
    "PHONE_INQUIRY": "call",
    "PARTNER_REFERRAL": "partner",
    "COLD_CALL": "call",
    "TRADE_SHOW": "compaign",
    "EMPLOYEE_REFERRAL": "existing customer",
    "ADVERTISEMENT": "compaign",
    "OTHER": "other",
}

OPPORTUNITY_STAGE_MAP = {
    "PROSPECTING": "PROSPECTING",
    "QUALIFICATION": "QUALIFICATION",
    "PROPOSAL": "PROPOSAL",
    "NEGOTIATION": "NEGOTIATION",
    "CLOSED_WON": "CLOSED_WON",
    "CLOSED_LOST": "CLOSED_LOST",
}

CASE_STATUS_MAP = {
    "OPEN": "New",
    "IN_PROGRESS": "Pending",
    "CLOSED": "Closed",
}

TASK_STATUS_MAP = {
    "Not Started": "New",
    "In Progress": "In Progress",
    "Completed": "Completed",
}

TASK_PRIORITY_MAP = {
    "High": "High",
    "Normal": "Medium",
    "Low": "Low",
}


class Command(BaseCommand):
    help = "Migrate data from Prisma PostgreSQL database to Django"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prisma_conn = None
        self.dry_run = False
        self.batch_size = 1000
        self.skip_existing = False
        self.stats = {
            "migrated": {},
            "skipped": {},
            "errors": {},
        }
        # ID mappings for relationship resolution
        self.user_to_profile = {}  # user_id -> {org_id: profile_id}
        self.org_map = {}  # old_org_id -> new_org_id

    def add_arguments(self, parser):
        parser.add_argument(
            "--db-host", type=str, required=True, help="Prisma database host"
        )
        parser.add_argument(
            "--db-port", type=int, default=5432, help="Prisma database port"
        )
        parser.add_argument(
            "--db-name", type=str, required=True, help="Prisma database name"
        )
        parser.add_argument(
            "--db-user", type=str, required=True, help="Prisma database user"
        )
        parser.add_argument(
            "--db-password", type=str, required=True, help="Prisma database password"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Validate without inserting"
        )
        parser.add_argument(
            "--batch-size", type=int, default=1000, help="Batch size for inserts"
        )
        parser.add_argument(
            "--skip-existing", action="store_true", help="Skip existing records"
        )
        parser.add_argument(
            "--only", type=str, help="Comma-separated list of models to migrate"
        )

    def handle(self, *args, **options):
        self.dry_run = options["dry_run"]
        self.batch_size = options["batch_size"]
        self.skip_existing = options["skip_existing"]
        only_models = options.get("only")

        if only_models:
            only_models = [m.strip().lower() for m in only_models.split(",")]

        self.stdout.write(self.style.NOTICE("Starting Prisma → Django migration"))

        if self.dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No data will be inserted")
            )

        # Connect to Prisma database
        try:
            self.prisma_conn = psycopg2.connect(
                host=options["db_host"],
                port=options["db_port"],
                database=options["db_name"],
                user=options["db_user"],
                password=options["db_password"],
                cursor_factory=RealDictCursor,
            )
            self.stdout.write(self.style.SUCCESS("Connected to Prisma database"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to connect to Prisma database: {e}")
            )
            return

        try:
            # Migration order (respects dependencies)
            migrations = [
                ("organization", self.migrate_organizations),
                ("user", self.migrate_users),
                ("profile", self.migrate_profiles),
                ("teams", self.migrate_teams),
                ("account", self.migrate_accounts),
                ("contact", self.migrate_contacts),
                ("accountcontacts", self.migrate_account_contacts),
                ("lead", self.migrate_leads),
                ("opportunity", self.migrate_opportunities),
                ("case", self.migrate_cases),
                ("solution", self.migrate_solutions),
                ("task", self.migrate_tasks),
                ("product", self.migrate_products),
                ("comment", self.migrate_comments),
                ("board", self.migrate_boards),
                ("boardmember", self.migrate_board_members),
                ("boardcolumn", self.migrate_board_columns),
                ("boardtask", self.migrate_board_tasks),
                ("contactsubmission", self.migrate_contact_submissions),
            ]

            for model_name, migration_func in migrations:
                if only_models and model_name not in only_models:
                    continue

                self.stdout.write(f"\nMigrating {model_name}...")
                try:
                    migration_func()
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error migrating {model_name}: {e}")
                    )
                    logger.exception(f"Error migrating {model_name}")
                    self.stats["errors"][model_name] = str(e)

            # Print summary
            self.print_summary()

        finally:
            if self.prisma_conn:
                self.prisma_conn.close()

    def print_summary(self):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("MIGRATION SUMMARY"))
        self.stdout.write("=" * 60)

        for model, count in self.stats["migrated"].items():
            self.stdout.write(f"  {model}: {count} migrated")

        if self.stats["skipped"]:
            self.stdout.write("\nSkipped:")
            for model, count in self.stats["skipped"].items():
                self.stdout.write(f"  {model}: {count} skipped")

        if self.stats["errors"]:
            self.stdout.write(self.style.ERROR("\nErrors:"))
            for model, error in self.stats["errors"].items():
                self.stdout.write(f"  {model}: {error}")

    def execute_query(self, query, params=None):
        """Execute a query on Prisma database and return results"""
        with self.prisma_conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_or_none(self, model, **kwargs):
        """Get object or return None"""
        try:
            return model.objects.get(**kwargs)
        except model.DoesNotExist:
            return None

    def migrate_organizations(self):
        """Migrate Organization → Org"""
        query = """
            SELECT id, name, "createdAt", "updatedAt", "isActive"
            FROM "Organization"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if self.skip_existing and Org.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            if not self.dry_run:
                import uuid

                api_key = str(uuid.uuid4())
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO organization (id, name, api_key, is_active, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            is_active = EXCLUDED.is_active,
                            updated_at = EXCLUDED.updated_at
                    """,
                        [
                            row["id"],
                            row["name"],
                            api_key,
                            row["isActive"],
                            row["createdAt"],
                            row["updatedAt"],
                        ],
                    )

            self.org_map[row["id"]] = row["id"]
            migrated += 1

        self.stats["migrated"]["Organization"] = migrated
        self.stats["skipped"]["Organization"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} organizations"))

    def migrate_users(self):
        """Migrate User → User (Django)"""
        query = """
            SELECT id, email, name, "profilePhoto", "isActive",
                   "createdAt", "updatedAt"
            FROM "User"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if self.skip_existing and User.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            # Split name into first/last (Django User doesn't have name field directly)
            name = row["name"] or ""
            name_parts = name.split(" ", 1)

            if not self.dry_run:
                # Truncate profile_pic to 1000 chars if needed
                profile_pic = row["profilePhoto"]
                if profile_pic and len(profile_pic) > 1000:
                    profile_pic = profile_pic[:1000]

                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO users (id, email, profile_pic, is_active, is_staff, is_superuser, password, last_login)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            email = EXCLUDED.email,
                            profile_pic = EXCLUDED.profile_pic,
                            is_active = EXCLUDED.is_active
                    """,
                        [
                            row["id"],
                            row["email"],
                            profile_pic,
                            row["isActive"],
                            False,  # is_staff
                            False,  # is_superuser
                            "",  # password (needs to be reset)
                            None,  # last_login
                        ],
                    )

            migrated += 1

        self.stats["migrated"]["User"] = migrated
        self.stats["skipped"]["User"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} users"))

    def migrate_profiles(self):
        """Migrate UserOrganization → Profile"""
        query = """
            SELECT uo.id, uo."userId", uo."organizationId", uo.role, uo."joinedAt",
                   u.phone, u.email
            FROM "UserOrganization" uo
            JOIN "User" u ON u.id = uo."userId"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            profile_id = row["id"]

            if self.skip_existing and Profile.objects.filter(id=profile_id).exists():
                skipped += 1
                continue

            # Map role
            role = "ADMIN" if row["role"] == "ADMIN" else "USER"
            is_org_admin = row["role"] == "ADMIN"

            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO profile (
                            id, user_id, org_id, role, is_active,
                            is_organization_admin, has_sales_access, has_marketing_access,
                            created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            role = EXCLUDED.role,
                            is_organization_admin = EXCLUDED.is_organization_admin
                    """,
                        [
                            profile_id,
                            row["userId"],
                            row["organizationId"],
                            role,
                            True,  # is_active
                            is_org_admin,
                            True,  # has_sales_access
                            True,  # has_marketing_access
                            row["joinedAt"],
                            row["joinedAt"],
                        ],
                    )

            # Store mapping for later use
            if row["userId"] not in self.user_to_profile:
                self.user_to_profile[row["userId"]] = {}
            self.user_to_profile[row["userId"]][row["organizationId"]] = profile_id

            migrated += 1

        self.stats["migrated"]["Profile"] = migrated
        self.stats["skipped"]["Profile"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} profiles"))

    def migrate_teams(self):
        """Teams don't exist in Prisma - skip"""
        self.stats["migrated"]["Teams"] = 0
        self.stdout.write("  No teams in Prisma schema - skipping")

    def migrate_accounts(self):
        """Migrate Account → Account"""
        query = """
            SELECT id, name, industry, website, phone,
                   street, city, state, "postalCode", country,
                   "annualRevenue", description, "numberOfEmployees",
                   "createdAt", "updatedAt", "ownerId", "organizationId", "isActive"
            FROM "Account"
            WHERE "isDeleted" = false
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if self.skip_existing and Account.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO accounts (
                            id, name, industry, website, phone,
                            address_line, city, state, postcode, country,
                            annual_revenue, description, number_of_employees,
                            created_at, updated_at, org_id, is_active
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            updated_at = EXCLUDED.updated_at
                    """,
                        [
                            row["id"],
                            row["name"],
                            row["industry"].upper() if row["industry"] else None,
                            row["website"],
                            row["phone"],
                            row["street"],
                            row["city"],
                            row["state"],
                            row["postalCode"],
                            (
                                row["country"][:2] if row["country"] else None
                            ),  # Convert to 2-letter code
                            row["annualRevenue"],
                            row["description"],
                            row["numberOfEmployees"],
                            row["createdAt"],
                            row["updatedAt"],
                            row["organizationId"],
                            row["isActive"],
                        ],
                    )

                # Add owner to assigned_to M2M
                owner_profile_id = self.user_to_profile.get(row["ownerId"], {}).get(
                    row["organizationId"]
                )
                if owner_profile_id:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO accounts_assigned_to (account_id, profile_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """,
                            [row["id"], owner_profile_id],
                        )

            migrated += 1

        self.stats["migrated"]["Account"] = migrated
        self.stats["skipped"]["Account"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} accounts"))

    def migrate_contacts(self):
        """Migrate Contact → Contact"""
        query = """
            SELECT id, "firstName", "lastName", email, phone,
                   title, department, street, city, state, "postalCode", country,
                   description, "createdAt", "updatedAt", "ownerId", "organizationId"
            FROM "Contact"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if self.skip_existing and Contact.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            # Skip contacts without organization
            if not row["organizationId"]:
                skipped += 1
                continue

            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO contacts (
                            id, first_name, last_name, email, phone,
                            title, department, address_line, city, state, postcode, country,
                            description, created_at, updated_at, org_id, is_active, do_not_call
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            updated_at = EXCLUDED.updated_at
                    """,
                        [
                            row["id"],
                            row["firstName"],
                            row["lastName"],
                            row["email"],
                            row["phone"],
                            row["title"],
                            row["department"],
                            row["street"],
                            row["city"],
                            row["state"],
                            row["postalCode"],
                            row["country"][:2] if row["country"] else None,
                            row["description"],
                            row["createdAt"],
                            row["updatedAt"],
                            row["organizationId"],
                            True,  # is_active
                            False,  # do_not_call
                        ],
                    )

                # Add owner to assigned_to M2M
                if row["organizationId"]:
                    owner_profile_id = self.user_to_profile.get(row["ownerId"], {}).get(
                        row["organizationId"]
                    )
                    if owner_profile_id:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                """
                                INSERT INTO contacts_assigned_to (contact_id, profile_id)
                                VALUES (%s, %s)
                                ON CONFLICT DO NOTHING
                            """,
                                [row["id"], owner_profile_id],
                            )

            migrated += 1

        self.stats["migrated"]["Contact"] = migrated
        self.stats["skipped"]["Contact"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} contacts"))

    def migrate_account_contacts(self):
        """Migrate AccountContactRelationship → Account.contacts M2M"""
        query = """
            SELECT "accountId", "contactId"
            FROM "AccountContactRelationship"
        """
        rows = self.execute_query(query)
        migrated = 0

        for row in rows:
            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO accounts_contacts (account_id, contact_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """,
                        [row["accountId"], row["contactId"]],
                    )
            migrated += 1

        self.stats["migrated"]["AccountContacts"] = migrated
        self.stdout.write(
            self.style.SUCCESS(f"  Migrated {migrated} account-contact relationships")
        )

    def migrate_leads(self):
        """Migrate Lead → Lead"""
        query = """
            SELECT id, "firstName", "lastName", email, phone, company, title,
                   status, "leadSource", industry, rating, description,
                   "createdAt", "updatedAt", "ownerId", "organizationId"
            FROM "Lead"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if self.skip_existing and Lead.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            # Map status and source
            status = LEAD_STATUS_MAP.get(row["status"], "assigned")
            source = (
                LEAD_SOURCE_MAP.get(row["leadSource"], "other")
                if row["leadSource"]
                else None
            )

            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO lead (
                            id, title, first_name, last_name, email, phone,
                            status, source, industry, rating, description,
                            created_at, updated_at, org_id, is_active, created_from_site
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            status = EXCLUDED.status,
                            updated_at = EXCLUDED.updated_at
                    """,
                        [
                            row["id"],
                            row["title"] or f"{row['firstName']} {row['lastName']}",
                            row["firstName"],
                            row["lastName"],
                            row["email"],
                            row["phone"],
                            status,
                            source,
                            row["industry"].upper() if row["industry"] else None,
                            row["rating"],
                            row["description"],
                            row["createdAt"],
                            row["updatedAt"],
                            row["organizationId"],
                            True,  # is_active
                            False,  # created_from_site
                        ],
                    )

                # Add owner to assigned_to M2M
                owner_profile_id = self.user_to_profile.get(row["ownerId"], {}).get(
                    row["organizationId"]
                )
                if owner_profile_id:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO lead_assigned_to (lead_id, profile_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """,
                            [row["id"], owner_profile_id],
                        )

            migrated += 1

        self.stats["migrated"]["Lead"] = migrated
        self.stats["skipped"]["Lead"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} leads"))

    def migrate_opportunities(self):
        """Migrate Opportunity → Opportunity"""
        query = """
            SELECT id, name, amount, stage, "closeDate", probability,
                   type, description, "leadSource",
                   "createdAt", "updatedAt", "accountId", "ownerId", "organizationId"
            FROM "Opportunity"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if self.skip_existing and Opportunity.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            # Map stage
            stage = OPPORTUNITY_STAGE_MAP.get(row["stage"], "PROSPECTING")

            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO opportunity (
                            id, name, amount, stage, closed_on, probability,
                            opportunity_type, description, lead_source,
                            created_at, updated_at, account_id, org_id, is_active
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            stage = EXCLUDED.stage,
                            updated_at = EXCLUDED.updated_at
                    """,
                        [
                            row["id"],
                            row["name"],
                            row["amount"],
                            stage,
                            row["closeDate"],
                            int(row["probability"]) if row["probability"] else 0,
                            row["type"],
                            row["description"],
                            row["leadSource"],
                            row["createdAt"],
                            row["updatedAt"],
                            row["accountId"],
                            row["organizationId"],
                            True,  # is_active
                        ],
                    )

                # Add owner to assigned_to M2M
                owner_profile_id = self.user_to_profile.get(row["ownerId"], {}).get(
                    row["organizationId"]
                )
                if owner_profile_id:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO opportunity_assigned_to (opportunity_id, profile_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """,
                            [row["id"], owner_profile_id],
                        )

            migrated += 1

        # Migrate opportunity contacts M2M
        self.migrate_opportunity_contacts()

        self.stats["migrated"]["Opportunity"] = migrated
        self.stats["skipped"]["Opportunity"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} opportunities"))

    def migrate_opportunity_contacts(self):
        """Migrate Opportunity-Contact M2M relationship"""
        query = """
            SELECT "A" as opportunity_id, "B" as contact_id
            FROM "_ContactToOpportunity"
        """
        try:
            rows = self.execute_query(query)
            for row in rows:
                if not self.dry_run:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO opportunity_contacts (opportunity_id, contact_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """,
                            [row["opportunity_id"], row["contact_id"]],
                        )
        except Exception as e:
            logger.warning(f"Could not migrate opportunity contacts: {e}")

    def migrate_cases(self):
        """Migrate Case → Case"""
        query = """
            SELECT id, subject, status, description, priority, type, "closedAt",
                   "createdAt", "updatedAt", "accountId", "contactId", "ownerId", "organizationId"
            FROM "Case"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if self.skip_existing and Case.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            # Map status
            status = CASE_STATUS_MAP.get(row["status"], "New")

            # Map priority
            priority = (
                row["priority"]
                if row["priority"] in ["Low", "Normal", "High", "Urgent"]
                else "Normal"
            )

            # Map case type
            case_type = ""
            if row["type"]:
                type_lower = row["type"].lower()
                if "question" in type_lower:
                    case_type = "Question"
                elif "problem" in type_lower:
                    case_type = "Problem"
                else:
                    case_type = "Incident"

            if not self.dry_run:
                # Truncate name to 64 chars if needed
                case_name = row["subject"]
                if case_name and len(case_name) > 64:
                    case_name = case_name[:64]

                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO "case" (
                            id, name, status, description, priority, case_type, closed_on,
                            created_at, updated_at, account_id, org_id, is_active
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            status = EXCLUDED.status,
                            updated_at = EXCLUDED.updated_at
                    """,
                        [
                            row["id"],
                            case_name,
                            status,
                            row["description"],
                            priority,
                            case_type,
                            row["closedAt"].date() if row["closedAt"] else None,
                            row["createdAt"],
                            row["updatedAt"],
                            row["accountId"],
                            row["organizationId"],
                            True,  # is_active
                        ],
                    )

                # Add owner to assigned_to M2M
                owner_profile_id = self.user_to_profile.get(row["ownerId"], {}).get(
                    row["organizationId"]
                )
                if owner_profile_id:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO case_assigned_to (case_id, profile_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """,
                            [row["id"], owner_profile_id],
                        )

                # Add contact to contacts M2M
                if row["contactId"]:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO case_contacts (case_id, contact_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """,
                            [row["id"], row["contactId"]],
                        )

            migrated += 1

        self.stats["migrated"]["Case"] = migrated
        self.stats["skipped"]["Case"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} cases"))

    def migrate_solutions(self):
        """Migrate Solution → Solution"""
        query = """
            SELECT id, title, description, status, "isPublished",
                   "createdAt", "updatedAt", "organizationId"
            FROM "Solution"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if self.skip_existing and Solution.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            # Map status
            status = row["status"].lower() if row["status"] else "draft"
            if status not in ["draft", "reviewed", "approved"]:
                status = "draft"

            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO solution (
                            id, title, description, status, is_published,
                            created_at, updated_at, org_id
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            title = EXCLUDED.title,
                            status = EXCLUDED.status,
                            updated_at = EXCLUDED.updated_at
                    """,
                        [
                            row["id"],
                            row["title"],
                            row["description"],
                            status,
                            row["isPublished"],
                            row["createdAt"],
                            row["updatedAt"],
                            row["organizationId"],
                        ],
                    )

            migrated += 1

        # Migrate solution-case M2M
        self.migrate_solution_cases()

        self.stats["migrated"]["Solution"] = migrated
        self.stats["skipped"]["Solution"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} solutions"))

    def migrate_solution_cases(self):
        """Migrate Solution-Case M2M relationship"""
        query = """
            SELECT "A" as case_id, "B" as solution_id
            FROM "_CaseToSolution"
        """
        try:
            rows = self.execute_query(query)
            for row in rows:
                if not self.dry_run:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO solution_cases (solution_id, case_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """,
                            [row["solution_id"], row["case_id"]],
                        )
        except Exception as e:
            logger.warning(f"Could not migrate solution cases: {e}")

    def migrate_tasks(self):
        """Migrate Task → Task"""
        query = """
            SELECT id, subject, status, priority, "dueDate", description,
                   "createdAt", "updatedAt", "accountId", "contactId",
                   "ownerId", "organizationId"
            FROM "Task"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if self.skip_existing and Task.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            # Map status and priority
            status = TASK_STATUS_MAP.get(row["status"], "New")
            priority = TASK_PRIORITY_MAP.get(row["priority"], "Medium")

            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO task (
                            id, title, status, priority, due_date, description,
                            created_at, updated_at, account_id, org_id
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            title = EXCLUDED.title,
                            status = EXCLUDED.status,
                            updated_at = EXCLUDED.updated_at
                    """,
                        [
                            row["id"],
                            row["subject"],
                            status,
                            priority,
                            row["dueDate"].date() if row["dueDate"] else None,
                            row["description"],
                            row["createdAt"],
                            row["updatedAt"],
                            row["accountId"],
                            row["organizationId"],
                        ],
                    )

                # Add owner to assigned_to M2M
                owner_profile_id = self.user_to_profile.get(row["ownerId"], {}).get(
                    row["organizationId"]
                )
                if owner_profile_id:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO task_assigned_to (task_id, profile_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """,
                            [row["id"], owner_profile_id],
                        )

                # Add contact to contacts M2M
                if row["contactId"]:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO task_contacts (task_id, contact_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """,
                            [row["id"], row["contactId"]],
                        )

            migrated += 1

        self.stats["migrated"]["Task"] = migrated
        self.stats["skipped"]["Task"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} tasks"))

    def migrate_products(self):
        """Migrate Product → Product"""
        query = """
            SELECT id, name, code, description, "unitPrice", active,
                   "createdAt", "updatedAt", "organizationId"
            FROM "Product"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if self.skip_existing and Product.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO product (
                            id, name, sku, description, price, is_active,
                            created_at, updated_at, org_id
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            price = EXCLUDED.price,
                            updated_at = EXCLUDED.updated_at
                    """,
                        [
                            row["id"],
                            row["name"],
                            row["code"],
                            row["description"],
                            row["unitPrice"],
                            row["active"],
                            row["createdAt"],
                            row["updatedAt"],
                            row["organizationId"],
                        ],
                    )

            migrated += 1

        self.stats["migrated"]["Product"] = migrated
        self.stats["skipped"]["Product"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} products"))

    def migrate_comments(self):
        """Migrate Comment → Comment (using GenericFK)"""
        query = """
            SELECT id, body, "createdAt", "updatedAt", "authorId", "organizationId",
                   "caseId", "opportunityId", "leadId", "accountId", "contactId", "taskId"
            FROM "Comment"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        # Get content types
        content_types = {
            "case": ContentType.objects.get_for_model(Case),
            "opportunity": ContentType.objects.get_for_model(Opportunity),
            "lead": ContentType.objects.get_for_model(Lead),
            "account": ContentType.objects.get_for_model(Account),
            "contact": ContentType.objects.get_for_model(Contact),
            "task": ContentType.objects.get_for_model(Task),
        }

        for row in rows:
            if self.skip_existing and Comment.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            # Determine content type and object ID
            content_type = None
            object_id = None

            if row["caseId"]:
                content_type = content_types["case"]
                object_id = row["caseId"]
            elif row["opportunityId"]:
                content_type = content_types["opportunity"]
                object_id = row["opportunityId"]
            elif row["leadId"]:
                content_type = content_types["lead"]
                object_id = row["leadId"]
            elif row["accountId"]:
                content_type = content_types["account"]
                object_id = row["accountId"]
            elif row["contactId"]:
                content_type = content_types["contact"]
                object_id = row["contactId"]
            elif row["taskId"]:
                content_type = content_types["task"]
                object_id = row["taskId"]
            else:
                skipped += 1
                continue

            # Get profile ID for author
            author_profile_id = self.user_to_profile.get(row["authorId"], {}).get(
                row["organizationId"]
            )

            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO comment (
                            id, content_type_id, object_id, comment, commented_on,
                            commented_by_id, org_id, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            comment = EXCLUDED.comment,
                            updated_at = EXCLUDED.updated_at
                    """,
                        [
                            row["id"],
                            content_type.id,
                            object_id,
                            (
                                row["body"][:255] if row["body"] else ""
                            ),  # Truncate to 255 chars
                            row["createdAt"],
                            author_profile_id,
                            row["organizationId"],
                            row["createdAt"],
                            row["updatedAt"],
                        ],
                    )

            migrated += 1

        self.stats["migrated"]["Comment"] = migrated
        self.stats["skipped"]["Comment"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} comments"))

    def migrate_boards(self):
        """Migrate Board → Board"""
        query = """
            SELECT id, name, description, "createdAt", "updatedAt",
                   "ownerId", "organizationId"
            FROM "Board"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if self.skip_existing and Board.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            # Get owner profile
            owner_profile_id = self.user_to_profile.get(row["ownerId"], {}).get(
                row["organizationId"]
            )

            if not owner_profile_id:
                skipped += 1
                continue

            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO board (
                            id, name, description, is_archived,
                            created_at, updated_at, owner_id, org_id
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            updated_at = EXCLUDED.updated_at
                    """,
                        [
                            row["id"],
                            row["name"],
                            row["description"],
                            False,  # is_archived
                            row["createdAt"],
                            row["updatedAt"],
                            owner_profile_id,
                            row["organizationId"],
                        ],
                    )

            migrated += 1

        self.stats["migrated"]["Board"] = migrated
        self.stats["skipped"]["Board"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} boards"))

    def migrate_board_members(self):
        """Migrate BoardMember → BoardMember"""
        query = """
            SELECT bm.id, bm."boardId", bm."userId", bm.role, bm."createdAt",
                   b."organizationId"
            FROM "BoardMember" bm
            JOIN "Board" b ON b.id = bm."boardId"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if self.skip_existing and BoardMember.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            # Get profile ID for user
            profile_id = self.user_to_profile.get(row["userId"], {}).get(
                row["organizationId"]
            )

            if not profile_id:
                skipped += 1
                continue

            # Map role
            role = row["role"].lower() if row["role"] else "member"
            if role not in ["owner", "admin", "member"]:
                role = "member"

            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO board_member (
                            id, board_id, profile_id, role, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            role = EXCLUDED.role
                    """,
                        [
                            row["id"],
                            row["boardId"],
                            profile_id,
                            role,
                            row["createdAt"],
                            row["createdAt"],
                        ],
                    )

            migrated += 1

        self.stats["migrated"]["BoardMember"] = migrated
        self.stats["skipped"]["BoardMember"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} board members"))

    def migrate_board_columns(self):
        """Migrate BoardColumn → BoardColumn"""
        query = """
            SELECT id, name, "order", "boardId", "createdAt", "updatedAt"
            FROM "BoardColumn"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if self.skip_existing and BoardColumn.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO board_column (
                            id, name, "order", color, board_id, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            "order" = EXCLUDED."order",
                            updated_at = EXCLUDED.updated_at
                    """,
                        [
                            row["id"],
                            row["name"],
                            row["order"],
                            "#6B7280",  # default color
                            row["boardId"],
                            row["createdAt"],
                            row["updatedAt"],
                        ],
                    )

            migrated += 1

        self.stats["migrated"]["BoardColumn"] = migrated
        self.stats["skipped"]["BoardColumn"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} board columns"))

    def migrate_board_tasks(self):
        """Migrate BoardTask → BoardTask"""
        query = """
            SELECT id, title, description, "order", "dueDate", completed,
                   "columnId", "assigneeId", "createdAt", "updatedAt"
            FROM "BoardTask"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if self.skip_existing and BoardTask.objects.filter(id=row["id"]).exists():
                skipped += 1
                continue

            # Get board org to find profile
            board_org_query = """
                SELECT b."organizationId"
                FROM "BoardColumn" bc
                JOIN "Board" b ON b.id = bc."boardId"
                WHERE bc.id = %s
            """
            org_rows = self.execute_query(board_org_query, [row["columnId"]])
            org_id = org_rows[0]["organizationId"] if org_rows else None

            if not self.dry_run:
                completed_at = row["createdAt"] if row["completed"] else None

                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO board_task (
                            id, title, description, "order", priority,
                            due_date, completed_at, column_id, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            title = EXCLUDED.title,
                            description = EXCLUDED.description,
                            updated_at = EXCLUDED.updated_at
                    """,
                        [
                            row["id"],
                            row["title"],
                            row["description"],
                            row["order"],
                            "medium",  # default priority
                            row["dueDate"],
                            completed_at,
                            row["columnId"],
                            row["createdAt"],
                            row["updatedAt"],
                        ],
                    )

                # Add assignee to assigned_to M2M
                if row["assigneeId"] and org_id:
                    profile_id = self.user_to_profile.get(row["assigneeId"], {}).get(
                        org_id
                    )
                    if profile_id:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                """
                                INSERT INTO board_task_assigned_to (boardtask_id, profile_id)
                                VALUES (%s, %s)
                                ON CONFLICT DO NOTHING
                            """,
                                [row["id"], profile_id],
                            )

            migrated += 1

        self.stats["migrated"]["BoardTask"] = migrated
        self.stats["skipped"]["BoardTask"] = skipped
        self.stdout.write(self.style.SUCCESS(f"  Migrated {migrated} board tasks"))

    def migrate_contact_submissions(self):
        """Migrate ContactSubmission → ContactFormSubmission"""
        query = """
            SELECT id, name, email, message, reason,
                   "ipAddress", "userAgent", referrer, "createdAt"
            FROM "ContactSubmission"
        """
        rows = self.execute_query(query)
        migrated = 0
        skipped = 0

        for row in rows:
            if (
                self.skip_existing
                and ContactFormSubmission.objects.filter(id=row["id"]).exists()
            ):
                skipped += 1
                continue

            # Map reason
            reason = row["reason"].lower() if row["reason"] else "general"
            valid_reasons = ["general", "sales", "support", "partnership", "other"]
            if reason not in valid_reasons:
                reason = "other"

            if not self.dry_run:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO contact_form_submission (
                            id, name, email, message, reason,
                            ip_address, user_agent, referrer, status, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            email = EXCLUDED.email
                    """,
                        [
                            row["id"],
                            row["name"],
                            row["email"],
                            row["message"],
                            reason,
                            row["ipAddress"],
                            row["userAgent"],
                            row["referrer"],
                            "new",  # status
                            row["createdAt"],
                            row["createdAt"],
                        ],
                    )

            migrated += 1

        self.stats["migrated"]["ContactSubmission"] = migrated
        self.stats["skipped"]["ContactSubmission"] = skipped
        self.stdout.write(
            self.style.SUCCESS(f"  Migrated {migrated} contact submissions")
        )
