"""`security_audit_log` has no RLS policy, so nothing may serve it unfiltered.

`common/0036` removed the per-tenant policies from this table, because its
`org` is nullable by design and the insert check refused every org-less row:
the failed logins, invalid API keys and cross-org attempts the ledger exists
to record. Full reasoning is in that migration.

Removing a safety net is only safe while nothing depends on it. Today
`SecurityAuditLog` is write-only: `AuditLogger` creates rows, `common/models.py`
re-exports the name, and one pack test reads it. The moment an endpoint serves
these rows, a missing `org=` filter becomes a cross-tenant disclosure of
usernames, IP addresses and authentication failures with no policy underneath
to catch it. These tests fail when that day arrives, next to the reason.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

from common.audit_log import SecurityAuditLog
from common.rls import ORG_SCOPED_TABLES

BACKEND_ROOT = Path(settings.BASE_DIR)

# Modules allowed to name the model. Each is a non-serving use.
ALLOWED = {
    "common/audit_log.py",  # defines it and is the only writer
    "common/models.py",  # re-exports the name for existing imports
    "common/migrations",  # schema history
    "common/tests",  # this guard, plus one pack test asserting a row was written
}


def _python_files():
    for path in BACKEND_ROOT.rglob("*.py"):
        rel = path.relative_to(BACKEND_ROOT).as_posix()
        if rel.startswith((".venv/", "venv/", "staticfiles/")):
            continue
        yield rel, path


def test_the_table_is_not_registered_for_rls():
    """Registering it again would reinstate the refusal `0036` removed."""
    assert "security_audit_log" not in ORG_SCOPED_TABLES


def test_the_model_is_not_referenced_by_any_serving_module():
    offenders = []
    for rel, path in _python_files():
        if any(rel.startswith(prefix) for prefix in ALLOWED):
            continue
        if re.search(r"\bSecurityAuditLog\b", path.read_text()):
            offenders.append(rel)

    assert not offenders, (
        "SecurityAuditLog is now referenced outside the modules that only "
        "write or re-export it:\n  " + "\n  ".join(sorted(offenders)) + "\n\n"
        "That table has no RLS policy (see common/migrations/0036). If this "
        "reference serves rows to a client, the org filter has to be explicit "
        "in the ORM and object-level authorization has to be checked, because "
        "there is no policy to fall back on. Add the module here once you have "
        "done both."
    )


@pytest.mark.django_db
def test_a_row_with_no_org_can_be_written():
    """The behaviour `0036` restores.

    On PostgreSQL under a policy-bound role this insert used to raise
    `InsufficientPrivilege`, swallowed by `AuditLogger._log`. On SQLite it
    always succeeded, which is why the suite never noticed.
    """
    row = SecurityAuditLog.objects.create(
        event_type="LOGIN_FAILURE",
        org=None,
        user=None,
        description="wrong password",
        success=False,
    )

    assert row.pk is not None
    assert SecurityAuditLog.objects.filter(pk=row.pk).exists()
