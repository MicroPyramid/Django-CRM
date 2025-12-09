# Migration to remove Company model and add company_name field to Lead

from django.db import migrations, models


def migrate_company_to_company_name(apps, schema_editor):
    """Copy Company.name to Lead.company_name for all leads with a company."""
    Lead = apps.get_model("leads", "Lead")
    for lead in Lead.objects.filter(company__isnull=False).select_related("company"):
        lead.company_name = lead.company.name
        lead.save(update_fields=["company_name"])


def reverse_migrate_company_name_to_company(apps, schema_editor):
    """Reverse migration - create Company records from company_name."""
    Lead = apps.get_model("leads", "Lead")
    Company = apps.get_model("leads", "Company")

    for lead in Lead.objects.filter(company_name__isnull=False).exclude(
        company_name=""
    ):
        company, _ = Company.objects.get_or_create(
            name=lead.company_name,
            org=lead.org,
        )
        lead.company = company
        lead.save(update_fields=["company"])


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0003_add_full_conversion_fields"),
    ]

    operations = [
        # Step 1: Add company_name field to Lead
        migrations.AddField(
            model_name="lead",
            name="company_name",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Company Name",
            ),
        ),
        # Step 2: Migrate data from Company.name to Lead.company_name
        migrations.RunPython(
            migrate_company_to_company_name,
            reverse_migrate_company_name_to_company,
        ),
        # Step 3: Remove the company FK from Lead
        migrations.RemoveField(
            model_name="lead",
            name="company",
        ),
        # Step 4: Delete the Company model
        migrations.DeleteModel(
            name="Company",
        ),
    ]
