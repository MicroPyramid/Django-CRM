from django.db import connection, migrations

from common.rls import get_disable_policy_sql, get_enable_policy_sql

# Registered in common/rls/__init__.py:ORG_SCOPED_TABLES.
TABLE = "interaction"


def enable_rls(apps, schema_editor):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(get_enable_policy_sql(TABLE))


def disable_rls(apps, schema_editor):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(get_disable_policy_sql(TABLE))


class Migration(migrations.Migration):
    # RLS policy creation cannot run inside an atomic block.
    atomic = False

    dependencies = [
        ("interactions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(enable_rls, reverse_code=disable_rls),
    ]
