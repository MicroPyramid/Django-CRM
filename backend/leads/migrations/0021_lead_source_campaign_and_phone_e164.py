"""Move `Lead.source` into the lead source keys, and fill `Lead.phone_e164`.

A stored source that names a key once case and surrounding spaces are set aside
becomes that key: the legacy lead keys (`compaign` becomes `campaign`), the old
deal values (`WEBSITE`, `Website` and `WEB` become `web form`) and every
default key or label ("Referral" becomes `referral`). Anything else, such as
free text from an import, is kept exactly as stored rather than guessed at.

`lead` is under FORCE ROW LEVEL SECURITY keyed on `app.current_org`, which is
empty during a migration, so an unscoped query reads and writes nothing in
production (common/0042 explains the backfill that once cost). Both functions
walk the orgs, which are not org-scoped, and set the context for each.

The E.164 rule is the live `common.phones.to_e164`, as `Lead.save` uses it.
Reverse: `campaign` goes back to `compaign` for the older code and other values
stay; the backfill is a no-op, since the older code never reads the column.
"""

from django.db import migrations, transaction

from common.phones import to_e164

BATCH_SIZE = 1000

# Matched against a stored value lowered and stripped. Frozen here, so a later
# change to the defaults cannot change what this did.
SOURCE_KEYS = {
    **{
        key: key
        for key in (
            "call",
            "email",
            "existing customer",
            "partner",
            "public relations",
            "campaign",
            "other",
            "web form",
            "meta ads",
            "google ads",
            "linkedin ads",
            "directory or marketplace",
            "whatsapp",
            "referral",
            "walk-in",
        )
    },
    "compaign": "campaign",
    "website": "web form",
    "web": "web form",
}


def source_key(value):
    """The key ``value`` names, or None when it names none."""
    if not isinstance(value, str):
        return None
    return SOURCE_KEYS.get(value.strip().lower())


def _each_org(apps, schema_editor, per_org):
    connection = schema_editor.connection
    is_postgres = connection.vendor == "postgresql"

    def set_context(value):
        if not is_postgres:
            return
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.current_org', %s, false)", [value])

    Org = apps.get_model("common", "Org")
    try:
        for org_id, country in (
            Org.objects.order_by("pk").values_list("id", "default_country").iterator()
        ):
            set_context(str(org_id))
            per_org(org_id, country)
    finally:
        set_context("")


def map_lead_sources(apps, schema_editor):
    Lead = apps.get_model("leads", "Lead")

    def per_org(org_id, _country):
        stored = (
            Lead.objects.filter(org_id=org_id)
            .exclude(source__isnull=True)
            .exclude(source="")
            .order_by()
            .values_list("source", flat=True)
            .distinct()
        )
        for value in list(stored):
            key = source_key(value)
            if key is not None and key != value:
                Lead.objects.filter(org_id=org_id, source=value).update(source=key)

    _each_org(apps, schema_editor, per_org)


def rename_campaign_to_compaign(apps, schema_editor):
    Lead = apps.get_model("leads", "Lead")

    def per_org(org_id, _country):
        Lead.objects.filter(org_id=org_id, source="campaign").update(source="compaign")

    _each_org(apps, schema_editor, per_org)


def backfill_lead_phone_e164(apps, schema_editor):
    Lead = apps.get_model("leads", "Lead")

    def per_org(org_id, country):
        rows = (
            Lead.objects.filter(org_id=org_id)
            .exclude(phone__isnull=True)
            .exclude(phone="")
            .only("id", "phone")
            .order_by("pk")
        )
        last = None
        while True:
            page = rows if last is None else rows.filter(pk__gt=last)
            with transaction.atomic(using=schema_editor.connection.alias):
                batch = list(page[:BATCH_SIZE])
                if not batch:
                    return
                for lead in batch:
                    lead.phone_e164 = to_e164(lead.phone, country)
                Lead.objects.bulk_update(
                    [lead for lead in batch if lead.phone_e164], ["phone_e164"]
                )
            last = batch[-1].pk

    _each_org(apps, schema_editor, per_org)


class Migration(migrations.Migration):
    # One transaction per batch, so row locks are released as it goes. Both
    # steps are idempotent, so a rerun after a partial failure is safe.
    atomic = False

    dependencies = [
        ("leads", "0020_enable_rls_lead_source_and_intake"),
    ]

    operations = [
        migrations.RunPython(map_lead_sources, rename_campaign_to_compaign),
        migrations.RunPython(backfill_lead_phone_e164, migrations.RunPython.noop),
    ]
