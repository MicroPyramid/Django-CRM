"""A form's `lead_source` becomes a key from the org's lead source list.

The column drops its fixed choices, widens to a `LeadSource.key`, and new forms
default to `web form`. Stored `compaign` becomes `campaign`, as on leads
(leads/0021). `web_form` is under FORCE ROW LEVEL SECURITY keyed on
`app.current_org`, which is empty during a migration, so the rename walks the
orgs and sets the context for each (common/0042 explains why).
"""

from django.db import migrations, models


def _rename(apps, schema_editor, old, new):
    connection = schema_editor.connection
    is_postgres = connection.vendor == "postgresql"
    Org = apps.get_model("common", "Org")
    WebForm = apps.get_model("webforms", "WebForm")

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
            WebForm.objects.filter(org_id=org_id, lead_source=old).update(
                lead_source=new
            )
    finally:
        set_context("")


def rename_compaign_to_campaign(apps, schema_editor):
    _rename(apps, schema_editor, "compaign", "campaign")


def rename_campaign_to_compaign(apps, schema_editor):
    _rename(apps, schema_editor, "campaign", "compaign")


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0057_portalaccesstoken_lead_intake"),
        ("webforms", "0004_rotation_assignment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="webform",
            name="lead_source",
            field=models.CharField(default="web form", max_length=64),
        ),
        migrations.RunPython(rename_compaign_to_campaign, rename_campaign_to_compaign),
    ]
