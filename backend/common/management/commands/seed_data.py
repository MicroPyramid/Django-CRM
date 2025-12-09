"""
Management command to seed test data for the CRM application.

Usage:
    python manage.py seed_data --email admin@example.com
    python manage.py seed_data --email admin@example.com --orgs 2 --leads 100 --seed 42
    python manage.py seed_data --email admin@example.com --clear --no-input
"""

import random
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from crum import impersonate
from faker import Faker

from common.models import Org, Profile, Tags, Teams, User
from common.rls import get_set_context_sql
from common.utils import (
    CASE_TYPE,
    COUNTRIES,
    CURRENCY_CODES,
    INDCHOICES,
    LEAD_SOURCE,
    LEAD_STATUS,
    OPPORTUNITY_TYPES,
    PRIORITY_CHOICE,
    SOURCES,
    STAGES,
    STATUS_CHOICE,
)
from invoices.seed import InvoiceSeeder


class Command(BaseCommand):
    help = "Seed the database with realistic test CRM data"

    # Status distribution weights (simulate realistic data)
    LEAD_STATUS_WEIGHTS = {
        "assigned": 40,
        "in process": 30,
        "converted": 15,
        "recycled": 10,
        "closed": 5,
    }
    OPP_STAGE_WEIGHTS = {
        "PROSPECTING": 20,
        "QUALIFICATION": 20,
        "PROPOSAL": 20,
        "NEGOTIATION": 20,
        "CLOSED_WON": 10,
        "CLOSED_LOST": 10,
    }
    CASE_STATUS_WEIGHTS = {
        "New": 40,
        "Assigned": 25,
        "Pending": 20,
        "Closed": 10,
        "Rejected": 5,
    }
    TASK_STATUS_WEIGHTS = {
        "New": 30,
        "In Progress": 40,
        "Completed": 30,
    }

    # Common tag names for CRM
    TAG_NAMES = [
        "Hot Lead",
        "Enterprise",
        "SMB",
        "Renewal",
        "Upsell",
        "High Priority",
        "Follow Up",
        "Decision Maker",
        "Influencer",
        "Champion",
        "At Risk",
        "New Customer",
        "VIP",
        "Partner Referral",
        "Inbound",
    ]

    # Team name templates
    TEAM_NAMES = [
        ("Sales Team", "Primary sales team handling all inbound leads"),
        ("Enterprise Sales", "Dedicated team for enterprise accounts"),
        ("SMB Team", "Small and medium business focused team"),
        ("Customer Success", "Post-sales customer success team"),
        ("Support Team", "Technical support and case management"),
        ("Marketing Ops", "Marketing operations and campaign management"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake = None
        self.admin_user = None
        self.invoice_seeder = None
        self.stats = {
            "orgs": 0,
            "users": 0,
            "profiles": 0,
            "teams": 0,
            "tags": 0,
            "contacts": 0,
            "accounts": 0,
            "leads": 0,
            "opportunities": 0,
            "cases": 0,
            "tasks": 0,
        }

    def add_arguments(self, parser):
        # Required
        parser.add_argument(
            "--email",
            type=str,
            required=True,
            help="Admin user email (required)",
        )

        # Entity counts
        parser.add_argument(
            "--orgs",
            type=int,
            default=1,
            help="Number of organizations to create (default: 1)",
        )
        parser.add_argument(
            "--users-per-org",
            type=int,
            default=3,
            help="Additional users per organization (default: 3)",
        )
        parser.add_argument(
            "--leads",
            type=int,
            default=20,
            help="Leads per organization (default: 20)",
        )
        parser.add_argument(
            "--accounts",
            type=int,
            default=10,
            help="Accounts per organization (default: 10)",
        )
        parser.add_argument(
            "--contacts",
            type=int,
            default=15,
            help="Contacts per organization (default: 15)",
        )
        parser.add_argument(
            "--opportunities",
            type=int,
            default=10,
            help="Opportunities per organization (default: 10)",
        )
        parser.add_argument(
            "--cases",
            type=int,
            default=5,
            help="Cases per organization (default: 5)",
        )
        parser.add_argument(
            "--tasks",
            type=int,
            default=10,
            help="Tasks per organization (default: 10)",
        )
        parser.add_argument(
            "--teams",
            type=int,
            default=2,
            help="Teams per organization (default: 2)",
        )
        parser.add_argument(
            "--tags",
            type=int,
            default=5,
            help="Tags per organization (default: 5)",
        )

        # Invoice-related arguments
        parser.add_argument(
            "--products",
            type=int,
            default=20,
            help="Products per organization (default: 20)",
        )
        parser.add_argument(
            "--invoices",
            type=int,
            default=50,
            help="Invoices per organization (default: 50)",
        )
        parser.add_argument(
            "--estimates",
            type=int,
            default=15,
            help="Estimates per organization (default: 15)",
        )
        parser.add_argument(
            "--recurring-invoices",
            type=int,
            default=5,
            help="Recurring invoices per organization (default: 5)",
        )
        parser.add_argument(
            "--invoice-templates",
            type=int,
            default=3,
            help="Invoice templates per organization (default: 3)",
        )

        # Options
        parser.add_argument(
            "--seed",
            type=int,
            help="Random seed for reproducibility",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="testpass123",
            help="Password for new users (default: testpass123)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing CRM data before seeding",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Skip confirmation prompts",
        )

    def handle(self, *args, **options):
        # Initialize Faker
        seed = options.get("seed")
        if seed:
            random.seed(seed)
            self.fake = Faker(["en_US"])
            Faker.seed(seed)
        else:
            self.fake = Faker(["en_US", "en_GB", "en_CA", "en_AU"])

        # Initialize InvoiceSeeder
        self.invoice_seeder = InvoiceSeeder(self.fake, self.stdout)

        self.stdout.write(self.style.MIGRATE_HEADING("Seeding CRM database..."))
        if seed:
            self.stdout.write(f"Using seed: {seed}")

        # Handle clear option
        if options["clear"]:
            self.handle_clear(options)

        # Get or create admin user
        self.admin_user = self.get_or_create_admin(
            options["email"], options["password"]
        )

        start_time = timezone.now()

        try:
            with transaction.atomic():
                with impersonate(self.admin_user):
                    self.seed_all(options)
        except Exception as e:
            raise CommandError(f"Seeding failed: {e}")

        elapsed = (timezone.now() - start_time).total_seconds()
        self.print_summary(elapsed)

    def handle_clear(self, options):
        """Handle the --clear option."""
        if not options["no_input"]:
            confirm = input(
                "This will delete existing CRM data (not users/orgs). Continue? [y/N]: "
            )
            if confirm.lower() != "y":
                raise CommandError("Operation cancelled.")

        self.stdout.write("Clearing existing CRM data...")
        self.clear_data()
        self.stdout.write(self.style.SUCCESS("Data cleared."))

    def clear_data(self):
        """Clear CRM data in reverse dependency order (preserves Users/Orgs/Profiles)."""
        from accounts.models import Account
        from cases.models import Case
        from contacts.models import Contact
        from leads.models import Lead
        from opportunity.models import Opportunity
        from tasks.models import Task

        # Clear invoice data first (depends on accounts/contacts)
        self.invoice_seeder.clear_invoice_data()

        # Delete in reverse dependency order
        Task.objects.all().delete()
        Case.objects.all().delete()
        Opportunity.objects.all().delete()
        Lead.objects.all().delete()
        Account.objects.all().delete()
        Contact.objects.all().delete()
        Teams.objects.all().delete()
        Tags.objects.all().delete()

        self.stdout.write("  Cleared: Tasks, Cases, Opportunities, Leads, Accounts, Contacts, Teams, Tags")

    def get_or_create_admin(self, email, password):
        """Get existing user or create new admin user."""
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f"Using existing user: {email}")
        except User.DoesNotExist:
            user = User.objects.create_user(email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Created user: {email}"))
            self.stats["users"] += 1
        return user

    def set_rls_context(self, org_id):
        """Set the RLS context for database operations."""
        with connection.cursor() as cursor:
            cursor.execute(get_set_context_sql(), [str(org_id)])

    def seed_all(self, options):
        """Main seeding orchestration."""
        for i in range(options["orgs"]):
            self.stdout.write(f"\n--- Organization {i + 1}/{options['orgs']} ---")
            org = self.create_org()
            # Set RLS context for this org before creating org-scoped data
            self.set_rls_context(org.id)
            profiles = self.create_profiles(
                org, options["users_per_org"], options["password"]
            )
            teams = self.create_teams(org, profiles, options["teams"])
            tags = self.create_tags(org, options["tags"])
            contacts = self.create_contacts(
                org, profiles, teams, tags, options["contacts"]
            )
            accounts = self.create_accounts(
                org, profiles, teams, tags, contacts, options["accounts"]
            )

            # Invoice prerequisites
            products = self.invoice_seeder.create_products(org, options["products"])
            templates = self.invoice_seeder.create_invoice_templates(
                org, options["invoice_templates"]
            )

            leads = self.create_leads(
                org, profiles, teams, tags, contacts, options["leads"]
            )
            opportunities = self.create_opportunities(
                org, profiles, teams, tags, contacts, accounts, options["opportunities"]
            )

            # Invoice entities
            invoices = self.invoice_seeder.create_invoices(
                org, profiles, teams, products, templates,
                accounts, contacts, opportunities, options["invoices"]
            )
            self.invoice_seeder.create_payments(org, invoices)
            self.invoice_seeder.create_estimates(
                org, profiles, teams, products, accounts, contacts, options["estimates"]
            )
            self.invoice_seeder.create_recurring_invoices(
                org, profiles, teams, products, accounts, contacts,
                options["recurring_invoices"]
            )

            cases = self.create_cases(
                org, profiles, teams, tags, contacts, accounts, options["cases"]
            )
            self.create_tasks(
                org,
                profiles,
                teams,
                tags,
                contacts,
                accounts,
                leads,
                opportunities,
                cases,
                options["tasks"],
            )

    def create_org(self):
        """Create an organization."""
        currencies = [c[0] for c in CURRENCY_CODES]
        countries = ["US", "GB", "CA", "AU", "DE", "FR", "IN"]

        org = Org.objects.create(
            name=self.fake.company(),
            default_currency=random.choice(currencies),
            default_country=random.choice(countries),
        )
        self.stats["orgs"] += 1
        self.stdout.write(
            f"  Created org: {org.name} ({org.default_currency}, {org.default_country})"
        )
        return org

    def create_profiles(self, org, user_count, password):
        """Create profiles for admin user and additional users."""
        profiles = []

        # Create admin profile in this org
        admin_profile, created = Profile.objects.get_or_create(
            user=self.admin_user,
            org=org,
            defaults={
                "role": "ADMIN",
                "has_sales_access": True,
                "has_marketing_access": True,
                "is_organization_admin": True,
                "is_active": True,
            },
        )
        profiles.append(admin_profile)
        if created:
            self.stats["profiles"] += 1

        # Create additional users for this org
        for i in range(user_count):
            email = f"user{i + 1}_{org.id.hex[:8]}@{self.fake.domain_name()}"
            user, user_created = User.objects.get_or_create(
                email=email,
                defaults={"is_active": True},
            )
            if user_created:
                user.set_password(password)
                user.save()
                self.stats["users"] += 1

            profile = Profile.objects.create(
                user=user,
                org=org,
                role="USER",
                has_sales_access=random.choice([True, False]),
                has_marketing_access=random.choice([True, False]),
                is_active=True,
                phone=self.fake.phone_number()[:20],
            )
            profiles.append(profile)
            self.stats["profiles"] += 1

        self.stdout.write(f"  Created {len(profiles)} profiles (1 admin, {user_count} users)")
        return profiles

    def create_teams(self, org, profiles, count):
        """Create teams and assign random profiles."""
        teams = []
        team_templates = random.sample(
            self.TEAM_NAMES, min(count, len(self.TEAM_NAMES))
        )

        for name, description in team_templates:
            team = Teams.objects.create(
                name=name,
                description=description,
                org=org,
            )
            # Assign random profiles to team
            num_members = random.randint(1, min(3, len(profiles)))
            team.users.add(*random.sample(profiles, num_members))
            teams.append(team)
            self.stats["teams"] += 1

        self.stdout.write(f"  Created {len(teams)} teams")
        return teams

    def create_tags(self, org, count):
        """Create tags for the organization."""
        tags = []
        tag_names = random.sample(self.TAG_NAMES, min(count, len(self.TAG_NAMES)))

        for name in tag_names:
            tag = Tags.objects.create(name=name, org=org)
            tags.append(tag)
            self.stats["tags"] += 1

        self.stdout.write(f"  Created {len(tags)} tags")
        return tags

    def create_contacts(self, org, profiles, teams, tags, count):
        """Create contacts."""
        from contacts.models import Contact

        contacts = []
        for _ in range(count):
            contact = Contact.objects.create(
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name(),
                email=self.fake.company_email(),
                phone=self.fake.phone_number()[:20],
                organization=self.fake.company(),
                title=self.fake.job(),
                department=random.choice(
                    ["Sales", "Marketing", "Engineering", "Finance", "Operations", "HR"]
                ),
                address_line=self.fake.street_address(),
                city=self.fake.city(),
                state=self.fake.state_abbr(),
                postcode=self.fake.postcode(),
                country=random.choice(["US", "GB", "CA", "AU"]),
                description=self.fake.paragraph() if random.random() > 0.5 else None,
                org=org,
            )

            # Add M2M relationships
            self._add_assignments(contact, profiles, teams, tags)
            contacts.append(contact)
            self.stats["contacts"] += 1

        self.stdout.write(f"  Created {len(contacts)} contacts")
        return contacts

    def create_accounts(self, org, profiles, teams, tags, contacts, count):
        """Create accounts with contacts."""
        from accounts.models import Account

        accounts = []
        industries = [c[0] for c in INDCHOICES]

        for _ in range(count):
            account = Account.objects.create(
                name=self.fake.company(),
                email=self.fake.company_email(),
                phone=self.fake.phone_number()[:20],
                website=self.fake.url(),
                industry=random.choice(industries),
                number_of_employees=random.choice(
                    [10, 50, 100, 250, 500, 1000, 5000, 10000]
                ),
                annual_revenue=Decimal(
                    str(random.randint(100000, 10000000))
                ),
                currency=org.default_currency,
                address_line=self.fake.street_address(),
                city=self.fake.city(),
                state=self.fake.state_abbr(),
                postcode=self.fake.postcode(),
                country=org.default_country or "US",
                description=self.fake.paragraph() if random.random() > 0.5 else None,
                org=org,
            )

            # Add contacts to account
            if contacts:
                num_contacts = random.randint(1, min(3, len(contacts)))
                account.contacts.add(*random.sample(contacts, num_contacts))

            # Add M2M relationships
            self._add_assignments(account, profiles, teams, tags)
            accounts.append(account)
            self.stats["accounts"] += 1

        self.stdout.write(f"  Created {len(accounts)} accounts")
        return accounts

    def create_leads(self, org, profiles, teams, tags, contacts, count):
        """Create leads."""
        from leads.models import Lead

        leads = []
        industries = [c[0] for c in INDCHOICES]
        sources = [c[0] for c in LEAD_SOURCE]
        ratings = ["HOT", "WARM", "COLD"]

        # Lead title templates for realistic data
        lead_title_templates = [
            "Enterprise Deal",
            "Website Inquiry",
            "Demo Request",
            "Partnership Opportunity",
            "Inbound Lead",
            "Referral Opportunity",
            "Trade Show Contact",
            "Product Inquiry",
            "Upgrade Opportunity",
            "Expansion Deal",
            "New Business Inquiry",
            "Consultation Request",
        ]

        for _ in range(count):
            status = self._weighted_choice(self.LEAD_STATUS_WEIGHTS)
            # Generate a title - either from templates or using faker
            if random.random() > 0.3:
                title = random.choice(lead_title_templates)
            else:
                title = f"{self.fake.catch_phrase()} Opportunity"

            lead = Lead.objects.create(
                title=title,
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name(),
                email=self.fake.company_email(),
                phone=self.fake.phone_number()[:20],
                company_name=self.fake.company(),
                job_title=self.fake.job(),
                website=self.fake.url() if random.random() > 0.5 else None,
                status=status,
                source=random.choice(sources),
                industry=random.choice(industries),
                rating=random.choice(ratings),
                opportunity_amount=Decimal(str(random.randint(5000, 500000))),
                currency=org.default_currency,
                probability=random.randint(10, 90),
                close_date=self.fake.date_between(
                    start_date="today", end_date="+90d"
                ) if random.random() > 0.3 else None,
                address_line=self.fake.street_address(),
                city=self.fake.city(),
                state=self.fake.state_abbr(),
                postcode=self.fake.postcode(),
                country=org.default_country or "US",
                description=self.fake.paragraph() if random.random() > 0.5 else None,
                org=org,
            )

            # Optionally link contacts
            if contacts and random.random() > 0.7:
                num_contacts = random.randint(1, min(2, len(contacts)))
                lead.contacts.add(*random.sample(contacts, num_contacts))

            # Add M2M relationships
            self._add_assignments(lead, profiles, teams, tags)
            leads.append(lead)
            self.stats["leads"] += 1

        self.stdout.write(f"  Created {len(leads)} leads")
        return leads

    def create_opportunities(
        self, org, profiles, teams, tags, contacts, accounts, count
    ):
        """Create opportunities linked to accounts."""
        from opportunity.models import Opportunity

        opportunities = []
        opp_types = [c[0] for c in OPPORTUNITY_TYPES]
        sources = [c[0] for c in SOURCES]

        for _ in range(count):
            stage = self._weighted_choice(self.OPP_STAGE_WEIGHTS)
            account = random.choice(accounts) if accounts else None

            opp = Opportunity.objects.create(
                name=f"{self.fake.catch_phrase()} Deal",
                account=account,
                stage=stage,
                opportunity_type=random.choice(opp_types),
                amount=Decimal(str(random.randint(10000, 1000000))),
                currency=org.default_currency,
                probability=self._stage_to_probability(stage),
                closed_on=self.fake.date_between(
                    start_date="today", end_date="+120d"
                ) if stage not in ["CLOSED_WON", "CLOSED_LOST"] else self.fake.date_between(
                    start_date="-30d", end_date="today"
                ),
                lead_source=random.choice(sources),
                description=self.fake.paragraph() if random.random() > 0.5 else None,
                org=org,
            )

            # Set closed_by for closed opportunities
            if stage in ["CLOSED_WON", "CLOSED_LOST"]:
                opp.closed_by = random.choice(profiles)
                opp.save()

            # Link contacts
            if contacts:
                num_contacts = random.randint(1, min(2, len(contacts)))
                opp.contacts.add(*random.sample(contacts, num_contacts))

            # Add M2M relationships
            self._add_assignments(opp, profiles, teams, tags)
            opportunities.append(opp)
            self.stats["opportunities"] += 1

        self.stdout.write(f"  Created {len(opportunities)} opportunities")
        return opportunities

    def create_cases(self, org, profiles, teams, tags, contacts, accounts, count):
        """Create cases linked to accounts."""
        from cases.models import Case

        cases = []
        case_types = [c[0] for c in CASE_TYPE]
        priorities = [c[0] for c in PRIORITY_CHOICE]

        for _ in range(count):
            status = self._weighted_choice(self.CASE_STATUS_WEIGHTS)
            account = random.choice(accounts) if accounts else None

            case = Case.objects.create(
                name=f"{self.fake.bs().title()} Issue"[:64],
                status=status,
                priority=random.choice(priorities),
                case_type=random.choice(case_types),
                account=account,
                closed_on=self.fake.date_between(
                    start_date="-30d", end_date="today"
                ) if status == "Closed" else None,
                description=self.fake.paragraph(),
                org=org,
            )

            # Link contacts
            if contacts:
                num_contacts = random.randint(1, min(2, len(contacts)))
                case.contacts.add(*random.sample(contacts, num_contacts))

            # Add M2M relationships
            self._add_assignments(case, profiles, teams, tags)
            cases.append(case)
            self.stats["cases"] += 1

        self.stdout.write(f"  Created {len(cases)} cases")
        return cases

    def create_tasks(
        self,
        org,
        profiles,
        teams,
        tags,
        contacts,
        accounts,
        leads,
        opportunities,
        cases,
        count,
    ):
        """Create tasks linked to various parent entities."""
        from tasks.models import Task

        tasks = []
        priorities = ["Low", "Medium", "High"]

        for _ in range(count):
            status = self._weighted_choice(self.TASK_STATUS_WEIGHTS)

            # Determine parent entity (only one allowed)
            parent_type = random.choices(
                ["account", "opportunity", "case", "lead", "none"],
                weights=[30, 25, 25, 15, 5],
                k=1,
            )[0]

            task_data = {
                "title": self.fake.sentence(nb_words=5)[:200],
                "status": status,
                "priority": random.choice(priorities),
                "due_date": self.fake.date_between(
                    start_date="today", end_date="+30d"
                ) if status != "Completed" else self.fake.date_between(
                    start_date="-14d", end_date="today"
                ),
                "description": self.fake.paragraph() if random.random() > 0.5 else None,
                "org": org,
            }

            # Set parent entity
            if parent_type == "account" and accounts:
                task_data["account"] = random.choice(accounts)
            elif parent_type == "opportunity" and opportunities:
                task_data["opportunity"] = random.choice(opportunities)
            elif parent_type == "case" and cases:
                task_data["case"] = random.choice(cases)
            elif parent_type == "lead" and leads:
                task_data["lead"] = random.choice(leads)

            task = Task.objects.create(**task_data)

            # Link contacts
            if contacts and random.random() > 0.7:
                num_contacts = random.randint(1, min(2, len(contacts)))
                task.contacts.add(*random.sample(contacts, num_contacts))

            # Add M2M relationships
            self._add_assignments(task, profiles, teams, tags)
            tasks.append(task)
            self.stats["tasks"] += 1

        self.stdout.write(f"  Created {len(tasks)} tasks")
        return tasks

    def _add_assignments(self, instance, profiles, teams, tags):
        """Add common M2M assignments to an entity."""
        # Assign to profiles
        if profiles:
            num_assigned = random.randint(1, min(2, len(profiles)))
            instance.assigned_to.add(*random.sample(profiles, num_assigned))

        # Assign to team (70% chance)
        if teams and random.random() > 0.3:
            instance.teams.add(random.choice(teams))

        # Add tags (60% chance)
        if tags and random.random() > 0.4:
            num_tags = random.randint(1, min(3, len(tags)))
            instance.tags.add(*random.sample(tags, num_tags))

    def _weighted_choice(self, weights_dict):
        """Select a random key based on weights."""
        items = list(weights_dict.keys())
        weights = list(weights_dict.values())
        return random.choices(items, weights=weights, k=1)[0]

    def _stage_to_probability(self, stage):
        """Map opportunity stage to probability."""
        mapping = {
            "PROSPECTING": random.randint(5, 15),
            "QUALIFICATION": random.randint(15, 30),
            "PROPOSAL": random.randint(30, 50),
            "NEGOTIATION": random.randint(50, 75),
            "CLOSED_WON": 100,
            "CLOSED_LOST": 0,
        }
        return mapping.get(stage, 50)

    def print_summary(self, elapsed_seconds):
        """Print seeding summary."""
        # Merge invoice stats
        self.stats.update(self.invoice_seeder.stats)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Seeding complete!"))
        self.stdout.write("")
        self.stdout.write("Summary:")
        self.stdout.write(f"  Organizations: {self.stats['orgs']}")
        self.stdout.write(f"  Users: {self.stats['users']}")
        self.stdout.write(f"  Profiles: {self.stats['profiles']}")
        self.stdout.write(f"  Teams: {self.stats['teams']}")
        self.stdout.write(f"  Tags: {self.stats['tags']}")
        self.stdout.write(f"  Contacts: {self.stats['contacts']}")
        self.stdout.write(f"  Accounts: {self.stats['accounts']}")
        self.stdout.write(f"  Products: {self.stats['products']}")
        self.stdout.write(f"  Invoice Templates: {self.stats['invoice_templates']}")
        self.stdout.write(f"  Leads: {self.stats['leads']}")
        self.stdout.write(f"  Opportunities: {self.stats['opportunities']}")
        self.stdout.write(f"  Invoices: {self.stats['invoices']}")
        self.stdout.write(f"  Invoice Line Items: {self.stats['invoice_line_items']}")
        self.stdout.write(f"  Payments: {self.stats['payments']}")
        self.stdout.write(f"  Estimates: {self.stats['estimates']}")
        self.stdout.write(f"  Estimate Line Items: {self.stats['estimate_line_items']}")
        self.stdout.write(f"  Recurring Invoices: {self.stats['recurring_invoices']}")
        self.stdout.write(f"  Cases: {self.stats['cases']}")
        self.stdout.write(f"  Tasks: {self.stats['tasks']}")
        self.stdout.write("")
        self.stdout.write(f"Total time: {elapsed_seconds:.2f} seconds")
