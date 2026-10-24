from django.db import connection, migrations

from common.rls import get_disable_policy_sql, get_enable_policy_sql

# Registered in common/rls/__init__.py:ORG_SCOPED_TABLES. One list here so the
# enable and disable directions cannot drift apart.
TABLES = ["lead_source", "lead_intake", "lead_intake_event"]


def enable_rls(apps, schema_editor):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        for table in TABLES:
            cursor.execute(get_enable_policy_sql(table))


def disable_rls(apps, schema_editor):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        for table in TABLES:
            cursor.execute(get_disable_policy_sql(table))


class Migration(migrations.Migration):
    # RLS policy creation cannot run inside an atomic block.
    atomic = False

    dependencies = [
        ("leads", "0019_lead_sources_and_intakes"),
    ]

    operations = [
        migrations.RunPython(enable_rls, reverse_code=disable_rls),
    ]
