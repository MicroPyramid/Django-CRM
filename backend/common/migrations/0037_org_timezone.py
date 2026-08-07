from django.db import migrations, models

import common.validators

# The value of `settings.TIME_ZONE` immediately before orgs carried their own,
# captured here rather than read from settings on purpose: this change also
# moves that setting to "UTC", so by the time the migration runs the old value
# is gone. Every org that existed before this point has been getting its days
# in this zone, and a migration that silently shifted their day boundaries by
# five and a half hours would move invoices in and out of "overdue" overnight.
#
# New orgs default to UTC (the field default) and choose their own at creation.
TIME_ZONE_BEFORE_ORGS_HAD_ONE = "Asia/Kolkata"


def adopt_the_deployment_timezone(apps, schema_editor):
    """Give existing orgs the day they already had."""
    Org = apps.get_model("common", "Org")
    Org.objects.update(timezone=TIME_ZONE_BEFORE_ORGS_HAD_ONE)


def back_to_the_field_default(apps, schema_editor):
    Org = apps.get_model("common", "Org")
    Org.objects.update(timezone="UTC")


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0036_unscope_security_audit_log"),
    ]

    operations = [
        migrations.AddField(
            model_name="org",
            name="timezone",
            field=models.CharField(
                default="UTC",
                help_text="IANA timezone (e.g. America/New_York). Sets the org's day.",
                max_length=64,
                validators=[common.validators.validate_iana_timezone],
            ),
        ),
        migrations.RunPython(adopt_the_deployment_timezone, back_to_the_field_default),
    ]
