"""Carry saved list views over to the lead source keys.

leads/0021 and opportunity/0024 move lead and deal sources into the lead
source keys. A saved leads view filtering on `source`, or a deals view on
`lead_source`, would otherwise match nothing, so its stored values get the same
rule: a value that names a key once case and surrounding spaces are set aside
becomes that key, and anything else is kept as stored. A deal's `NONE` became
empty and has no key, so a view naming it is left as it is.

`saved_view` is under FORCE ROW LEVEL SECURITY keyed on `app.current_org`,
which is empty during a migration, so this walks the orgs and sets the context
for each (common/0042 explains why). Reverse is a no-op.
"""

from django.db import migrations

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

# The source parameter of each list that has one.
SOURCE_PARAMS = {"leads": "source", "opportunities": "lead_source"}


def _key(value):
    if not isinstance(value, str):
        return value
    return SOURCE_KEYS.get(value.strip().lower(), value)


def _mapped(value):
    if isinstance(value, list):
        return [_key(v) for v in value]
    return _key(value)


def map_saved_view_sources(apps, schema_editor):
    connection = schema_editor.connection
    is_postgres = connection.vendor == "postgresql"
    Org = apps.get_model("common", "Org")
    SavedView = apps.get_model("common", "SavedView")

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
            views = SavedView.objects.filter(org_id=org_id, module__in=SOURCE_PARAMS)
            for view in views:
                param = SOURCE_PARAMS[view.module]
                if not isinstance(view.filters, dict) or param not in view.filters:
                    continue
                filters = {**view.filters, param: _mapped(view.filters[param])}
                if filters != view.filters:
                    view.filters = filters
                    view.save(update_fields=["filters"])
    finally:
        set_context("")


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0057_portalaccesstoken_lead_intake"),
    ]

    operations = [
        migrations.RunPython(map_saved_view_sources, migrations.RunPython.noop),
    ]
