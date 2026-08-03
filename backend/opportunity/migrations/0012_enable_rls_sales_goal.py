# Enable Row-Level Security on the ``sales_goal`` table.
#
# SalesGoal is org-scoped (it has an ``org_id`` column and every view filters on
# it) but it was never registered in ORG_SCOPED_TABLES and no *source* migration
# stamped its RLS policies. A now-deleted migration once did on already-migrated
# databases, so those still carry the policies, but a fresh ``migrate`` from
# this source tree would ship ``sales_goal`` with no RLS at all, leaving tenant
# isolation resting solely on the ORM ``.filter(org=...)`` calls. This migration
# makes the protection reconstructible from source again.
#
# get_enable_policy_sql() opens with DROP POLICY IF EXISTS, so this is
# idempotent: it re-creates identical policies where they already exist and
# creates them where they do not.

from django.db import connection, migrations

from common.rls import get_disable_policy_sql, get_enable_policy_sql

TABLE = "sales_goal"


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
    atomic = False

    dependencies = [
        ("opportunity", "0011_opportunity_kanban_order"),
    ]

    operations = [
        migrations.RunPython(enable_rls, disable_rls),
    ]
