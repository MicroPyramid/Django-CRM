"""The guard on `opportunity/0015_drop_orphan_deal_pipeline_tables`.

The migration drops two tables that no model, no on-disk migration and no code
in either repo refers to, and removes three `django_migrations` rows whose
files were deleted from source. The reason it is safe to run against a
production database is the emptiness check, so that check is what these tests
pin: a table with rows in it survives, and its ledger rows survive with it.

These exercise `drop_orphans` directly rather than running the migration.
`migrate` in a test would need the whole graph rebuilt, and the interesting
behaviour is entirely inside this one function, which reads the live
connection rather than the historical model state.
"""

import importlib

import pytest
from django.db import connection

# `import ... from opportunity.migrations.0015_...` is a syntax error: the
# module name starts with a digit, which every migration name does.
_migration = importlib.import_module(
    "opportunity.migrations.0015_drop_orphan_deal_pipeline_tables"
)
DEAL_TABLE_ROWS = _migration.DEAL_TABLE_ROWS
ORPHAN_TABLES = _migration.ORPHAN_TABLES
SUPERSEDED_ROW = _migration.SUPERSEDED_ROW
drop_orphans = _migration.drop_orphans


@pytest.fixture(autouse=True)
def _no_orphans_left_behind():
    """Drop the fake tables before and after every test in this module.

    They are created with raw DDL rather than by a model, so nothing else
    knows about them, and a test that leaves one behind fails the next one
    with "table already exists" rather than with anything about the guard.
    """
    _drop_all()
    yield
    _drop_all()


def _drop_all():
    with connection.cursor() as cursor:
        for table in ORPHAN_TABLES:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")


def _create_orphans(cursor):
    """The two tables as a deleted migration once left them: `deal_stage`
    pointing at `deal_pipeline`, which is why the drop order matters."""
    cursor.execute("CREATE TABLE deal_pipeline (id varchar(32) PRIMARY KEY)")
    cursor.execute(
        "CREATE TABLE deal_stage ("
        "id varchar(32) PRIMARY KEY, "
        "pipeline_id varchar(32) REFERENCES deal_pipeline (id))"
    )


def _ledger(cursor):
    cursor.execute("SELECT name FROM django_migrations WHERE app = 'opportunity'")
    return {row[0] for row in cursor.fetchall()}


def _record(cursor, name):
    cursor.execute(
        "INSERT INTO django_migrations (app, name, applied) "
        "VALUES ('opportunity', %s, CURRENT_TIMESTAMP)",
        [name],
    )


@pytest.mark.django_db
class TestDroppingEmptyOrphans:
    def test_empty_tables_are_dropped_and_their_ledger_rows_go_with_them(self):
        with connection.cursor() as cursor:
            _create_orphans(cursor)
            for name in (SUPERSEDED_ROW, *DEAL_TABLE_ROWS):
                _record(cursor, name)

        drop_orphans(None, None)

        tables = set(connection.introspection.table_names())
        assert not (set(ORPHAN_TABLES) & tables)
        with connection.cursor() as cursor:
            remaining = _ledger(cursor)
        assert SUPERSEDED_ROW not in remaining
        assert not (set(DEAL_TABLE_ROWS) & remaining)

    def test_it_is_a_no_op_on_a_database_that_never_had_them(self):
        """A fresh `migrate` builds neither table, so this is the CI case and
        the one every new deployment hits."""
        with connection.cursor() as cursor:
            for name in (SUPERSEDED_ROW, *DEAL_TABLE_ROWS):
                _record(cursor, name)

        drop_orphans(None, None)

        with connection.cursor() as cursor:
            remaining = _ledger(cursor)
        assert SUPERSEDED_ROW not in remaining
        assert not (set(DEAL_TABLE_ROWS) & remaining)

    def test_it_leaves_the_real_opportunity_migrations_alone(self):
        """Only the three named rows are deleted. A `DELETE ... WHERE app =
        'opportunity'` that forgot its name filter would unapply the app."""
        with connection.cursor() as cursor:
            _create_orphans(cursor)
            before = _ledger(cursor)

        drop_orphans(None, None)

        with connection.cursor() as cursor:
            after = _ledger(cursor)
        assert after == before - {SUPERSEDED_ROW, *DEAL_TABLE_ROWS}
        assert "0014_opportunity_is_sample" in after


@pytest.mark.django_db
class TestTheEmptinessGuard:
    """The half that makes this safe to point at production."""

    def test_a_table_with_rows_is_not_dropped(self):
        with connection.cursor() as cursor:
            _create_orphans(cursor)
            cursor.execute("INSERT INTO deal_pipeline (id) VALUES ('keepme')")

        drop_orphans(None, None)

        tables = set(connection.introspection.table_names())
        assert "deal_pipeline" in tables
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM deal_pipeline")
            assert cursor.fetchone()[0] == 1

    def test_the_deal_ledger_rows_survive_with_the_table(self):
        """Those two rows are the only remaining record of where the table
        came from, so removing them while the table stays would make the
        database harder to explain, not easier."""
        with connection.cursor() as cursor:
            _create_orphans(cursor)
            cursor.execute("INSERT INTO deal_pipeline (id) VALUES ('keepme')")
            for name in (SUPERSEDED_ROW, *DEAL_TABLE_ROWS):
                _record(cursor, name)

        drop_orphans(None, None)

        with connection.cursor() as cursor:
            remaining = _ledger(cursor)
        assert set(DEAL_TABLE_ROWS) <= remaining
        # This one is independent: the tables it stamped policies on are all
        # covered by on-disk migrations now, so its row goes either way.
        assert SUPERSEDED_ROW not in remaining

    def test_an_empty_child_is_still_dropped_when_the_parent_is_kept(self):
        """`deal_stage` is dropped first, so a populated `deal_pipeline` does
        not shield an empty `deal_stage`. Each table is judged on its own."""
        with connection.cursor() as cursor:
            _create_orphans(cursor)
            cursor.execute("INSERT INTO deal_pipeline (id) VALUES ('keepme')")

        drop_orphans(None, None)

        tables = set(connection.introspection.table_names())
        assert "deal_stage" not in tables
        assert "deal_pipeline" in tables


@pytest.mark.django_db
def test_nothing_in_the_source_tree_refers_to_the_orphan_tables():
    """The premise of the whole migration.

    If a model ever grows one of these `db_table` names again, dropping it
    stops being a cleanup and starts being data loss, and this fails before
    that can ship.
    """
    from django.apps import apps

    live = {m._meta.db_table for m in apps.get_models()}
    assert not (set(ORPHAN_TABLES) & live), (
        "a model now maps to a table this migration drops when empty"
    )
