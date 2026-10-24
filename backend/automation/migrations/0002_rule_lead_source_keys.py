"""Carry automation rules over to the lead source keys.

leads/0021 and opportunity/0024 move lead and deal sources into the lead
source keys. A rule comparing or setting an old value would silently stop
working, so each rule's trigger value, condition values and set_field values
for `source` (a lead field) and `lead_source` (a deal field) get the same rule,
whatever object a set_field targets: a value that names a key once case and
surrounding spaces are set aside becomes that key, and anything else is kept.
A deal's `NONE` became empty and has no key, so a rule naming it is left for
its admin.

`automation_rule` is under FORCE ROW LEVEL SECURITY keyed on
`app.current_org`, which is empty during a migration, so this walks the orgs
and sets the context for each (common/0042 explains why). Reverse is a no-op.
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

SOURCE_FIELDS = ("source", "lead_source")


def _key(value):
    if not isinstance(value, str):
        return value
    return SOURCE_KEYS.get(value.strip().lower(), value)


def _mapped(field, value):
    if field not in SOURCE_FIELDS:
        return value
    if isinstance(value, list):
        return [_key(v) for v in value]
    return _key(value)


def _with_value(item, field_key="field"):
    if not isinstance(item, dict) or "value" not in item:
        return item
    return {**item, "value": _mapped(item.get(field_key), item["value"])}


def map_rule_source_values(apps, schema_editor):
    connection = schema_editor.connection
    is_postgres = connection.vendor == "postgresql"
    Org = apps.get_model("common", "Org")
    AutomationRule = apps.get_model("automation", "AutomationRule")

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
            for rule in AutomationRule.objects.filter(org_id=org_id):
                trigger = rule.trigger
                if isinstance(trigger, dict) and "to" in trigger:
                    trigger = {
                        **trigger,
                        "to": _mapped(trigger.get("field"), trigger["to"]),
                    }
                conditions = [_with_value(c) for c in rule.conditions or []]
                actions = [
                    _with_value(a)
                    if isinstance(a, dict) and a.get("type") == "set_field"
                    else a
                    for a in rule.actions or []
                ]
                if (trigger, conditions, actions) == (
                    rule.trigger,
                    rule.conditions,
                    rule.actions,
                ):
                    continue
                rule.trigger, rule.conditions, rule.actions = (
                    trigger,
                    conditions,
                    actions,
                )
                rule.save(update_fields=["trigger", "conditions", "actions"])
    finally:
        set_context("")


class Migration(migrations.Migration):
    dependencies = [
        ("automation", "0001_initial"),
        ("leads", "0021_lead_source_campaign_and_phone_e164"),
        ("opportunity", "0024_map_deal_lead_sources"),
    ]

    operations = [
        migrations.RunPython(map_rule_source_values, migrations.RunPython.noop),
    ]
