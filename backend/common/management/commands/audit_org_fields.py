"""
Management command to audit and fix nullable org fields.

This is part of Phase 1 multi-tenancy hardening - ensures all org-scoped
models have proper org field values before adding NOT NULL constraints.

Usage:
    python manage.py audit_org_fields --check     # Just check for issues
    python manage.py audit_org_fields --fix       # Attempt to fix issues
    python manage.py audit_org_fields --verbose   # Show detailed output
"""

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Audit and report on models with nullable org fields"

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="Check for null org values without making changes",
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Attempt to backfill null org values from related objects",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed information about each model",
        )

    def handle(self, *args, **options):
        check_only = options["check"]
        fix = options["fix"]
        verbose = options["verbose"]

        self.stdout.write(
            self.style.NOTICE("\n=== Multi-Tenancy Org Field Audit ===\n")
        )

        # Models that should have org but currently allow null
        models_with_nullable_org = [
            ("common", "Address"),
            ("common", "Tags"),
        ]

        # Models with proper org fields (for reference)
        models_with_required_org = [
            ("common", "Comment"),
            ("common", "Attachments"),
            ("common", "Document"),
            ("common", "Activity"),
            ("common", "Teams"),
            ("common", "APISettings"),
            ("accounts", "Account"),
            ("leads", "Lead"),
            ("contacts", "Contact"),
            ("opportunity", "Opportunity"),
            ("cases", "Case"),
            ("tasks", "Task"),
            ("invoices", "Invoice"),
        ]

        issues_found = []

        # Check models with nullable org
        self.stdout.write(
            self.style.WARNING("Checking models with nullable org fields:\n")
        )

        for app_label, model_name in models_with_nullable_org:
            try:
                model = apps.get_model(app_label, model_name)
                total_count = model.objects.count()
                null_count = model.objects.filter(org__isnull=True).count()

                if null_count > 0:
                    issues_found.append(
                        (app_label, model_name, null_count, total_count)
                    )
                    self.stdout.write(
                        f"  ❌ {app_label}.{model_name}: "
                        f"{null_count}/{total_count} records have NULL org"
                    )
                else:
                    self.stdout.write(
                        f"  ✅ {app_label}.{model_name}: "
                        f"All {total_count} records have org set"
                    )

                if verbose:
                    self._show_model_details(model)

            except LookupError:
                self.stdout.write(
                    self.style.ERROR(f"  ⚠️  {app_label}.{model_name}: Model not found")
                )

        # Check models with required org
        self.stdout.write(
            self.style.SUCCESS("\nChecking models with required org fields:\n")
        )

        for app_label, model_name in models_with_required_org:
            try:
                model = apps.get_model(app_label, model_name)
                total_count = model.objects.count()

                # Check if any null orgs exist (shouldn't happen but let's verify)
                if hasattr(model, "org"):
                    null_count = model.objects.filter(org__isnull=True).count()
                    if null_count > 0:
                        issues_found.append(
                            (app_label, model_name, null_count, total_count)
                        )
                        self.stdout.write(
                            f"  ❌ {app_label}.{model_name}: "
                            f"{null_count}/{total_count} records have NULL org (UNEXPECTED)"
                        )
                    else:
                        self.stdout.write(
                            f"  ✅ {app_label}.{model_name}: {total_count} records OK"
                        )

            except LookupError:
                if verbose:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠️  {app_label}.{model_name}: Model not found"
                        )
                    )

        # Summary
        self.stdout.write(self.style.NOTICE("\n=== Summary ===\n"))

        if issues_found:
            self.stdout.write(
                self.style.ERROR(
                    f"Found {len(issues_found)} models with NULL org values:\n"
                )
            )
            for app_label, model_name, null_count, total_count in issues_found:
                self.stdout.write(f"  - {app_label}.{model_name}: {null_count} records")

            if fix:
                self.stdout.write(self.style.WARNING("\nAttempting to fix issues...\n"))
                self._fix_null_orgs(issues_found)
            else:
                self.stdout.write(
                    self.style.NOTICE(
                        "\nRun with --fix to attempt automatic backfill, "
                        "or manually update records before adding NOT NULL constraints."
                    )
                )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "All models have proper org values! Ready for NOT NULL migration."
                )
            )

        # Recommendations
        self.stdout.write(self.style.NOTICE("\n=== Next Steps ===\n"))
        self.stdout.write(
            "1. Fix any NULL org values using --fix or manually\n"
            "2. Create migration to set org fields to NOT NULL:\n"
            "   - Address.org: null=False, blank=False\n"
            "   - Tags.org: null=False, blank=False\n"
            "3. Run: python manage.py makemigrations common\n"
            "4. Run: python manage.py migrate\n"
        )

    def _show_model_details(self, model):
        """Show detailed information about a model's org field configuration."""
        org_field = model._meta.get_field("org")
        self.stdout.write(
            f"    Field config: null={org_field.null}, blank={org_field.blank}, "
            f"related_name='{org_field.related_query_name()}'"
        )

    def _fix_null_orgs(self, issues):
        """Attempt to fix NULL org values by inferring from related objects."""
        from common.models import Address, Profile, Tags

        for app_label, model_name, null_count, total_count in issues:
            model = apps.get_model(app_label, model_name)

            if model_name == "Address":
                # Address can be inferred from Profile.address relationship
                fixed = 0
                for address in Address.objects.filter(org__isnull=True):
                    # Find profile that references this address
                    profile = Profile.objects.filter(address=address).first()
                    if profile and profile.org:
                        address.org = profile.org
                        address.save()
                        fixed += 1

                self.stdout.write(f"  Fixed {fixed}/{null_count} Address records")
                if fixed < null_count:
                    self.stdout.write(
                        self.style.WARNING(
                            f"    {null_count - fixed} records couldn't be fixed - "
                            "no related Profile found. Consider deleting orphaned records."
                        )
                    )

            elif model_name == "Tags":
                # Tags are harder - might need to check which entities use them
                self.stdout.write(
                    self.style.WARNING(
                        f"  Tags with NULL org need manual review. "
                        "Consider checking Account.tags, Lead.tags, etc. for usage."
                    )
                )

            else:
                self.stdout.write(
                    f"  {model_name}: Automatic fix not implemented. "
                    "Please fix manually."
                )
