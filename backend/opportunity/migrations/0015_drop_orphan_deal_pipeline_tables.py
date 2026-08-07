# Reconcile the three phantom ``opportunity`` rows in ``django_migrations``.
#
# ``0012_rls_opportunity_config``, ``0013_deal_pipeline_stage`` and
# ``0014_rls_deal_pipeline_stage`` are recorded as applied on every long-lived
# database, but the files were deleted from source. Nothing collides (the live
# 0012/0013 carry different names, so both applied fresh) and nothing breaks,
# but the effect is that ``showmigrations`` lists three migrations that do not
# exist and two tables, ``deal_pipeline`` and ``deal_stage``, sit in the schema
# with no model, no on-disk migration, and no reference anywhere in either
# repo. A fresh ``migrate`` builds neither, so CI and any disaster-recovery
# rebuild are already clean; it is the existing databases that disagree with
# their own source tree.
#
# EMPTINESS IS THE GUARD, and it is the whole reason this is safe to ship. A
# table with rows in it is data somebody may still want, whatever the source
# tree says, so this drops a table ONLY when it holds nothing. Where a table
# is not empty it is left exactly as it is, and the ledger rows that record
# where it came from are left with it, because deleting those would remove the
# only remaining trace of its origin. Dropping the table takes its RLS
# policies with it; there is nothing extra to clean up.
#
# ``0012_rls_opportunity_config`` is handled separately from the other two. It
# stamped policies on ``stage_aging_config``, ``opportunity_line_item`` and
# ``sales_goal``, all three of which are now stamped from on-disk migrations
# (opportunity/0012, opportunity/0013 and common/0011), so its row is noise
# regardless of what happens to the deal tables.

from django.db import connection, migrations

# Child first: `deal_stage.pipeline_id` is a foreign key to `deal_pipeline`,
# so the other order fails on a database that still has both.
ORPHAN_TABLES = ("deal_stage", "deal_pipeline")

# Recorded as applied, file long gone. Keyed by what has to be true before the
# row is safe to remove.
SUPERSEDED_ROW = "0012_rls_opportunity_config"
DEAL_TABLE_ROWS = ("0013_deal_pipeline_stage", "0014_rls_deal_pipeline_stage")


def drop_orphans(apps, schema_editor):
    existing = set(connection.introspection.table_names())
    kept = []

    with connection.cursor() as cursor:
        for table in ORPHAN_TABLES:
            if table not in existing:
                continue
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            if cursor.fetchone()[0]:
                kept.append(table)
                continue
            cursor.execute(f"DROP TABLE {table}")

        rows = [SUPERSEDED_ROW]
        # Only claim the deal-table history is resolved when the tables are
        # actually gone: either dropped just now, or never on this database in
        # the first place. `kept` holds every orphan that survived, so an empty
        # `kept` is exactly that condition.
        if not kept:
            rows.extend(DEAL_TABLE_ROWS)

        placeholders = ", ".join(["%s"] * len(rows))
        cursor.execute(
            "DELETE FROM django_migrations "
            f"WHERE app = 'opportunity' AND name IN ({placeholders})",
            rows,
        )

    if kept:
        print(f"  kept {', '.join(kept)}: not empty, so not dropped")


class Migration(migrations.Migration):
    dependencies = [
        ("opportunity", "0014_opportunity_is_sample"),
    ]

    operations = [
        # Not reversible, and deliberately not faked as such. A dropped empty
        # table cannot be restored by re-running anything here, and putting
        # the phantom ledger rows back would only recreate the confusion this
        # removes.
        migrations.RunPython(drop_orphans, migrations.RunPython.noop),
    ]
