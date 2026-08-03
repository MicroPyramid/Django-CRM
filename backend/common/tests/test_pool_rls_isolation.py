"""Proof that connection pooling cannot leak RLS context between tenants.

``app.current_org`` is a SESSION-scoped GUC (``set_config(..., false)``). It
survives the statement, the transaction, and the request. psycopg_pool does not
clear session state when a connection is returned: ``_reset_connection`` only
rolls back an open transaction. So a pool WITHOUT
``common.rls.pool.reset_rls_context`` hands the next borrower a backend still
scoped to the previous tenant, and every RLS policy on the database obediently
serves that borrower the wrong tenant's rows.

These tests build their own single-connection ``ConnectionPool`` rather than
driving Django's. Two reasons:

* ``max_size=1`` makes the second checkout provably the *same* backend. With
  the default pool size the next checkout may land on a connection that was
  never dirtied, and the test passes for the wrong reason. The assertions on
  ``pg_backend_pid()`` below exist to make that failure mode impossible.
* The default suite runs on SQLite (``crm/test_settings.py``), which has no
  ``set_config`` at all, so nothing here can be expressed through Django's
  ``connection``. Connection params are read from the same environment
  variables ``crm/settings.py`` uses, so this runs against whatever PostgreSQL
  the developer already has configured, and skips when there isn't one.

Note that these tests do NOT need a non-superuser role. They assert that the
session variable is cleared, which is upstream of RLS enforcement and therefore
observable even on a superuser dev database where RLS is inert. A companion
check that RLS then actually hides rows does need a non-superuser role; see
`RLS_SETUP.md`.
"""

import os

import pytest

psycopg = pytest.importorskip("psycopg")
psycopg_pool = pytest.importorskip("psycopg_pool")

from common.rls.pool import reset_rls_context  # noqa: E402

ORG_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ORG_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def _conn_kwargs():
    """Mirror the connection params crm/settings.py builds from the env."""
    return {
        "dbname": os.environ.get("DBNAME", "crm_db"),
        "user": os.environ.get("DBUSER", "postgres"),
        "password": os.environ.get("DBPASSWORD", "postgres"),
        "host": os.environ.get("DBHOST", "localhost"),
        "port": os.environ.get("DBPORT", "5432"),
        "autocommit": True,
    }


@pytest.fixture(scope="module", autouse=True)
def _require_postgres():
    try:
        with psycopg.connect(**_conn_kwargs(), connect_timeout=3):
            pass
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"PostgreSQL not reachable for pool isolation tests: {exc}")


def _single_connection_pool(reset):
    return psycopg_pool.ConnectionPool(
        kwargs=_conn_kwargs(),
        min_size=1,
        max_size=1,
        reset=reset,
        open=True,
        timeout=10,
    )


def _dirty(pool, org_id):
    """Borrow, set tenant context, hand the connection back. Returns the pid."""
    with pool.connection() as conn:
        pid = conn.execute("SELECT pg_backend_pid()").fetchone()[0]
        conn.execute("SELECT set_config('app.current_org', %s, false)", [org_id])
    return pid


def _observe(pool):
    """Borrow and report (pid, whatever app.current_org this borrower sees)."""
    with pool.connection() as conn:
        pid = conn.execute("SELECT pg_backend_pid()").fetchone()[0]
        seen = conn.execute(
            "SELECT current_setting('app.current_org', true)"
        ).fetchone()[0]
    return pid, seen


def test_reset_clears_tenant_context_before_the_next_borrower_sees_it():
    """The guard. Tenant A's org id must not survive into tenant B's checkout."""
    pool = _single_connection_pool(reset=reset_rls_context)
    try:
        pid_a = _dirty(pool, ORG_A)
        pid_b, seen = _observe(pool)
    finally:
        pool.close()

    assert pid_a == pid_b, (
        "test is inconclusive: the second checkout got a different backend, "
        "so nothing was proven about context surviving reuse"
    )
    assert seen in ("", None), (
        f"cross-tenant leak: the next borrower of backend {pid_b} sees "
        f"app.current_org={seen!r}, which RLS would resolve to another "
        f"tenant's rows"
    )


def test_without_the_reset_hook_the_context_does_leak():
    """Characterization, not a pinned bug.

    This asserts what a pool configured WITHOUT ``reset`` actually does, so the
    reason ``reset_rls_context`` is wired into DATABASES OPTIONS is recorded as
    an executable fact rather than a comment. If psycopg_pool ever starts
    clearing session state on its own, this test fails and the settings comment
    should be revisited. It is not asserting desired behaviour of our code.
    """
    pool = _single_connection_pool(reset=None)
    try:
        pid_a = _dirty(pool, ORG_A)
        pid_b, seen = _observe(pool)
    finally:
        pool.close()

    assert pid_a == pid_b, "inconclusive: different backend"
    assert seen == ORG_A, (
        "psycopg_pool appears to clear session state by itself now; if so the "
        "reset hook may no longer be load-bearing. Verify before relying on it."
    )


def test_reset_leaves_the_connection_idle_so_the_pool_keeps_reusing_it():
    """The silent-failure mode.

    ``ConnectionPool._reset_connection`` discards any connection the reset
    callback leaves in a non-IDLE transaction status. A reset that opens a
    transaction and forgets to commit therefore destroys and reopens a
    connection on every single checkout: correctness is preserved, but the pool
    silently stops pooling. That looks like a performance mystery, not an
    error, so it is asserted here.
    """
    pool = _single_connection_pool(reset=reset_rls_context)
    try:
        pids = set()
        for _ in range(15):
            pids.add(_dirty(pool, ORG_B))
        stats = pool.get_stats()
    finally:
        pool.close()

    assert len(pids) == 1, (
        f"the pool churned through {len(pids)} backends over 15 checkouts: the "
        f"reset callback is leaving connections non-IDLE and they are being "
        f"discarded"
    )
    assert stats.get("connections_num", 0) <= 2, (
        f"pool opened {stats.get('connections_num')} connections for a "
        f"max_size=1 pool, which means connections are being discarded"
    )
