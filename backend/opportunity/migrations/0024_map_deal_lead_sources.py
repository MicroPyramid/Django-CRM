"""Move `Opportunity.lead_source` into the lead source key space.

Deals used their own uppercase list, conversion copied the lead's lowercase
value in beside it (misspelt `compaign` included), and imports wrote free text.
A value that names a key once case and surrounding spaces are set aside
becomes that key: the old deal values (`WEBSITE`, `Website` and `WEB` become
`web form`, `NONE` becomes empty), the legacy lead keys and every default key
or label ("Referral" becomes `referral`). Anything else, such as "Trade Show",
is kept exactly as stored rather than guessed at.

`opportunity` is under FORCE ROW LEVEL SECURITY keyed on `app.current_org`,
which is empty during a migration, so this walks the orgs and sets the context
for each (common/0042 explains why). Reverse is a no-op: the older code shows
a value outside its list as it is, and a lowercase value from conversion was
already there before this ran.
"""

from django.db import migrations

# Matched against a stored value lowered and stripped. Frozen here, so a later
# change to the defaults cannot change what this did.
DEAL_SOURCE_KEYS = {
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
    "none": "",
}


def deal_source_key(value):
    """The key ``value`` names, or None when it names none."""
    if not isinstance(value, str):
        return None
    return DEAL_SOURCE_KEYS.get(value.strip().lower())


def map_deal_lead_sources(apps, schema_editor):
    connection = schema_editor.connection
    is_postgres = connection.vendor == "postgresql"
    Org = apps.get_model("common", "Org")
    Opportunity = apps.get_model("opportunity", "Opportunity")

    def set_context(value):
        if not is_postgres:
            return
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.current_org', %s, false)", [value])

    try:
        for org_id in (
            Org.objects.order_by("pk").values_list("id", flat=True).iterator()
        ):
            set_context(str(org_id))
            stored = (
                Opportunity.objects.filter(org_id=org_id)
                .exclude(lead_source__isnull=True)
                .exclude(lead_source="")
                .order_by()
                .values_list("lead_source", flat=True)
                .distinct()
            )
            for value in list(stored):
                key = deal_source_key(value)
                if key is not None and key != value:
                    Opportunity.objects.filter(org_id=org_id, lead_source=value).update(
                        lead_source=key
                    )
    finally:
        set_context("")


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0057_portalaccesstoken_lead_intake"),
        ("opportunity", "0023_opportunity_lead_source_keys"),
    ]

    operations = [
        migrations.RunPython(map_deal_lead_sources, migrations.RunPython.noop),
    ]
