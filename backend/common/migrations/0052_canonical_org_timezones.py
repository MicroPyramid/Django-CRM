from django.db import migrations

from common.org_time import canonical_timezone


def canonicalise_org_timezones(apps, schema_editor):
    """Rewrite every stored tz alias (``Asia/Calcutta``) to its zone (``Asia/Kolkata``).

    Browsers report some zones under their alias, and PostgreSQL may not know
    the alias, which made date queries fail for those orgs. ``Org.save`` now
    stores the canonical name; this fixes the rows written before it did. One
    UPDATE per distinct stored value, so it stays cheap on any number of orgs.
    """
    Org = apps.get_model("common", "Org")
    # order_by() first: Meta.ordering would add created_at to the DISTINCT.
    stored = Org.objects.order_by().values_list("timezone", flat=True).distinct()
    for name in list(stored):
        canonical = canonical_timezone(name)
        if canonical != name:
            Org.objects.filter(timezone=name).update(timezone=canonical)


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0051_invoice_numbering"),
    ]

    operations = [
        # The alias each row held is not recorded, and both names describe the
        # same zone, so there is nothing to restore on the way back.
        migrations.RunPython(canonicalise_org_timezones, migrations.RunPython.noop),
    ]
