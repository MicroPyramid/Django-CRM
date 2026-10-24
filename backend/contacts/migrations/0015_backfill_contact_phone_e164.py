"""Fill `Contact.phone_e164` for existing contacts, in batches.

`contacts` is under FORCE ROW LEVEL SECURITY keyed on `app.current_org`, which
is empty during a migration, so this walks the orgs and sets the context for
each, as leads/0021 does for leads. The rule is the live
`common.phones.to_e164`, as `Contact.save` uses it. Reverse is a no-op: the
older code never reads the column.
"""

from django.db import migrations, transaction

from common.phones import to_e164

BATCH_SIZE = 1000


def backfill_contact_phone_e164(apps, schema_editor):
    connection = schema_editor.connection
    is_postgres = connection.vendor == "postgresql"
    Org = apps.get_model("common", "Org")
    Contact = apps.get_model("contacts", "Contact")

    def set_context(value):
        if not is_postgres:
            return
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.current_org', %s, false)", [value])

    try:
        for org_id, country in (
            Org.objects.order_by("pk").values_list("id", "default_country").iterator()
        ):
            set_context(str(org_id))
            rows = (
                Contact.objects.filter(org_id=org_id)
                .exclude(phone__isnull=True)
                .exclude(phone="")
                .only("id", "phone")
                .order_by("pk")
            )
            last = None
            while True:
                page = rows if last is None else rows.filter(pk__gt=last)
                with transaction.atomic(using=connection.alias):
                    batch = list(page[:BATCH_SIZE])
                    if not batch:
                        break
                    for contact in batch:
                        contact.phone_e164 = to_e164(contact.phone, country)
                    Contact.objects.bulk_update(
                        [c for c in batch if c.phone_e164], ["phone_e164"]
                    )
                last = batch[-1].pk
    finally:
        set_context("")


class Migration(migrations.Migration):
    # One transaction per batch, so row locks are released as it goes. The
    # backfill is idempotent, so a rerun after a partial failure is safe.
    atomic = False

    dependencies = [
        ("common", "0057_portalaccesstoken_lead_intake"),
        ("contacts", "0014_contact_source_and_phone_e164"),
    ]

    operations = [
        migrations.RunPython(backfill_contact_phone_e164, migrations.RunPython.noop),
    ]
